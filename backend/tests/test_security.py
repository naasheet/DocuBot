from datetime import datetime
from jose import jwt
from app.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token

def test_password_hashing():
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)
    assert hashed != password

def test_hashing_randomness():
    password = "testpassword123"
    hashed1 = get_password_hash(password)
    hashed2 = get_password_hash(password)
    
    assert hashed1 != hashed2
    assert verify_password(password, hashed1)
    assert verify_password(password, hashed2)

def test_create_access_token():
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    
    assert token
    
    # Verify token content
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "test@example.com"
    assert "exp" in payload
    
    # Verify expiration is in the future
    assert payload["exp"] > datetime.utcnow().timestamp()