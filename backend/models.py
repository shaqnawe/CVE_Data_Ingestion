from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, SQLModel, Field
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class CVEReference(SQLModel):
    url: str
    source: Optional[str] = None


class CVEItem(SQLModel, table=True):
    __tablename__ = "cve_items"  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    cve_id: str = Field(index=True, unique=True)
    description: str
    published_date: str
    last_modified_date: str
    cvss_v3_score: Optional[float] = None
    severity: Optional[str] = None
    references: Optional[list[CVEReference]] = Field(sa_column=Column(JSONB))
    raw_data: dict = Field(sa_column=Column(JSONB))


class CVEPage(BaseModel):
    items: list[CVEItem]
    total: int
    skip: int
    limit: int


# User Models
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Optional[UserRole] = UserRole.USER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    created_at: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
