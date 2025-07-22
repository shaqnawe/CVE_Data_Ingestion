import pytest
from fastapi.testclient import TestClient
from backend.main import app
from sqlmodel import create_engine, Session
from backend.models import SQLModel
import backend.db

TEST_DATABASE_URL = "postgresql://postgres:yourpassword@localhost:5432/cve_test_db"
engine = create_engine(TEST_DATABASE_URL, echo=True)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


def override_get_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[backend.db.get_session] = override_get_session


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    reg_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
        "role": "admin",
    }
    reg_response = client.post("/auth/register", json=reg_data)
    print("Register response:", reg_response.status_code, reg_response.text)
    login_data = {"email": "testuser@example.com", "password": "testpassword"}
    response = client.post("/auth/login", json=login_data)
    print("Login response:", response.status_code, response.text, response.json())
    token = response.json().get("access_token")
    print("Token in conftest fixture:", token)
    assert token
    return {"Authorization": f"Bearer {token}"}
