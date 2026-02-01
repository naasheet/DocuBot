import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from jose import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.config import settings
from app.core.database import SessionLocal
from app.crud import user as crud_user
from app.schemas.user import UserCreate
# Import all models to ensure SQLAlchemy relationships are registered
from app.models import repository, chat, documentation

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(client: TestClient, db: Session):
    """Create a user for login tests."""
    email = "logintest@example.com"
    password = "TestPass123!"
    existing = crud_user.get_user_by_email(db, email)
    if existing:
        db.delete(existing)
        db.commit()
    user_in = UserCreate(email=email, password=password, full_name="Login Test")
    return crud_user.create_user(db, user_in)

def test_register_new_user(client: TestClient, db: Session):
    email = "newuser@example.com"
    # Cleanup
    existing = crud_user.get_user_by_email(db, email)
    if existing:
        db.delete(existing)
        db.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "New User"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == email
    assert "id" in data
    assert "password" not in data

def test_register_duplicate_email(client: TestClient, db: Session):
    email = "duplicate@example.com"
    # Cleanup
    existing = crud_user.get_user_by_email(db, email)
    if existing:
        db.delete(existing)
        db.commit()

    # Create user first
    user_in = UserCreate(email=email, password="password123", full_name="Duplicate Test")
    crud_user.create_user(db, user_in)

    # Try to register again
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 400, response.text
    assert "already exists" in response.json()["detail"]


def test_login_correct_credentials(client: TestClient, test_user):
    """Can login with correct credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "logintest@example.com", "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_wrong_password(client: TestClient, test_user):
    """Wrong credentials rejected."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "logintest@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401, response.text
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_wrong_email(client: TestClient, test_user):
    """Wrong email rejected."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "TestPass123!"},
    )
    assert response.status_code == 401, response.text
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_returns_valid_jwt(client: TestClient, test_user):
    """Returns valid JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "logintest@example.com", "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == str(test_user.id)
    assert "exp" in payload

def test_read_users_me(client: TestClient, test_user):
    """Test accessing a protected endpoint with a valid token."""
    # 1. Login to get access token
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "logintest@example.com", "password": "TestPass123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 2. Use token to access /me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "logintest@example.com"

def test_read_users_me_invalid_token(client: TestClient):
    """Test accessing a protected endpoint with an invalid token."""
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401

def test_github_login_redirect(client: TestClient):
    """Test that the login endpoint redirects to GitHub."""
    response = client.get("/api/v1/auth/github", allow_redirects=False)
    assert response.status_code == 307
    assert "github.com/login/oauth/authorize" in response.headers["location"]

def test_github_callback_success(client: TestClient, db: Session):
    """Test GitHub callback creates user and returns token."""
    # Use patch context manager to mock httpx.AsyncClient used in the endpoint
    with patch("app.api.v1.endpoints.auth.httpx.AsyncClient") as mock_client_cls:
        # Setup mock for AsyncClient context manager
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Mock access token response (POST)
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "gh_fake_token"}
        mock_client.post.return_value = mock_token_response

        # Mock user info response (GET)
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "login": "github_user",
            "name": "GitHub User",
            "email": "github_test@example.com"
        }
        mock_client.get.return_value = mock_user_response

        # Cleanup potential existing user from previous runs
        email = "github_test@example.com"
        existing = crud_user.get_user_by_email(db, email)
        if existing:
            db.delete(existing)
            db.commit()

        # Call the endpoint
        response = client.get("/api/v1/auth/github/callback?code=fake_code")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify user created in DB
        user = crud_user.get_user_by_email(db, email)
        assert user is not None
        assert user.email == email
        assert user.full_name == "GitHub User"