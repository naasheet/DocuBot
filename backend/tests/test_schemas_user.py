import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate

def test_user_create_valid():
    user = UserCreate(email="valid@example.com", password="password123", full_name="Valid User")
    assert user.email == "valid@example.com"
    assert user.password == "password123"

def test_user_create_invalid_email():
    with pytest.raises(ValidationError) as excinfo:
        UserCreate(email="not-an-email", password="password123")
    # Pydantic v2 error message check
    assert "value is not a valid email address" in str(excinfo.value)

def test_user_create_short_password():
    with pytest.raises(ValidationError) as excinfo:
        UserCreate(email="valid@example.com", password="short")
    assert "String should have at least 8 characters" in str(excinfo.value)