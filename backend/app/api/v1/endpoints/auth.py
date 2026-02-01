import logging
import secrets
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud import user as crud_user
from app.schemas.user import User, UserCreate, UserLogin, Token
from app.core.security import verify_password, create_access_token
from app.api import deps
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    try:
        logger.info(f"Registering user: {user_in.email}")
        # Check for duplicate email
        user = crud_user.get_user_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )
        
        # Create user (hashing is handled in CRUD)
        user = crud_user.create_user(db, user=user_in)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(e)}",
        )

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password. Returns a JWT access token.
    """
    # Verify email exists
    user = crud_user.get_user_by_email(db, email=credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    # Verify user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")

@router.post("/logout")
async def logout():
    return {"message": "Logout endpoint"}

@router.get("/github")
async def github_login():
    """
    Redirect to GitHub OAuth login.
    """
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&scope=user:email"
    )

@router.get("/github/callback", response_model=Token)
async def github_callback(code: str, db: Session = Depends(get_db)):
    """
    GitHub OAuth callback. Exchanges code for token and logs in user.
    """
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        
        data = response.json()
        if "error" in data:
            raise HTTPException(status_code=400, detail=data.get("error_description", "GitHub login failed"))
            
        access_token = data.get("access_token")
        
        # Fetch user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info from GitHub")
            
        github_user = user_response.json()
        
        # Get email (handle private emails)
        email = github_user.get("email")
        if not email:
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if emails_response.status_code == 200:
                emails = emails_response.json()
                # Get primary and verified email
                primary_email = next((e for e in emails if e.get("primary") and e.get("verified")), None)
                if primary_email:
                    email = primary_email["email"]
        
        if not email:
            raise HTTPException(status_code=400, detail="Could not retrieve verified email from GitHub")
            
        # Check if user exists or create new
        user = crud_user.get_user_by_email(db, email=email)
        if not user:
            password = secrets.token_urlsafe(32)
            user_in = UserCreate(
                email=email,
                password=password,
                full_name=github_user.get("name") or github_user.get("login")
            )
            user = crud_user.create_user(db, user=user_in)
        elif not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
            
        # Generate JWT
        access_token_jwt = create_access_token(data={"sub": str(user.id)})
        return Token(access_token=access_token_jwt, token_type="bearer")

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    """
    Fetch the current logged in user.
    """
    return current_user
