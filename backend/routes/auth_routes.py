from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from backend.db import get_session
from backend.models import (
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    UserRole,
)
from backend.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_active_user,
    require_role,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, session: Session = Depends(get_session)):
    """Register a new user."""
    # Check if user already exists
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    existing_username = session.exec(
        select(User).where(User.username == user_data.username)
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    now = datetime.utcnow().isoformat()

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        role=user_data.role or UserRole.USER,
        created_at=now,
        updated_at=now,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return UserResponse(
        id=user.id or 0,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, session: Session = Depends(get_session)):
    """Login and get access token."""
    # Find user by email
    user = session.exec(
        select(User).where(User.email == user_credentials.email)
    ).first()

    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Create access token
    access_token_expires = timedelta(minutes=60)  # Increased to 1 hour
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=60 * 60,  # 60 minutes in seconds
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id or 0,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    current_user: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """Get all users (admin only)."""
    users = session.exec(select(User)).all()
    return [
        UserResponse(
            id=user.id or 0,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]


@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """Activate a user (admin only)."""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_active = True
    user.updated_at = datetime.utcnow().isoformat()
    session.add(user)
    session.commit()

    return {"message": "User activated successfully"}


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """Deactivate a user (admin only)."""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_active = False
    user.updated_at = datetime.utcnow().isoformat()
    session.add(user)
    session.commit()

    return {"message": "User deactivated successfully"}


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """Update user role (admin only)."""
    from models import UserRole

    if role not in [r.value for r in UserRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role"
        )

    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.role = UserRole(role)
    user.updated_at = datetime.utcnow().isoformat()
    session.add(user)
    session.commit()

    return {"message": "User role updated successfully"}
