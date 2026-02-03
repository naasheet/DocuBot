import logging
import secrets
from datetime import datetime, timedelta, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud import user as crud_user
from app.schemas.user import (
    User,
    UserCreate,
    UserLogin,
    Token,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    LoginCodeRequest,
    UserNameUpdate,
)
from app.core.security import verify_password, create_access_token, hash_one_time_code, verify_one_time_code
from app.api import deps
from app.config import settings
from app.core.rate_limit import limiter
from app.services.email import send_email

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
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
@limiter.limit("20/minute")
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
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

@router.post("/forgot", response_model=ForgotPasswordResponse)
@limiter.limit("5/minute")
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Send a reset or login code to the user's email.
    """
    user = crud_user.get_user_by_email(db, email=payload.email)
    if user and user.is_active:
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = hash_one_time_code(code)
        now = datetime.now(timezone.utc)
        if payload.method == "reset":
            expires_at = now + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
            user.reset_code_hash = code_hash
            user.reset_code_expires_at = expires_at
            subject = "DocuBot password reset code"
            body = (
                "Use this code to reset your DocuBot password:\n\n"
                f"{code}\n\n"
                f"This code expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes."
            )
        else:
            expires_at = now + timedelta(minutes=settings.LOGIN_CODE_EXPIRE_MINUTES)
            user.login_code_hash = code_hash
            user.login_code_expires_at = expires_at
            subject = "DocuBot login code"
            body = (
                "Use this code to log in to DocuBot:\n\n"
                f"{code}\n\n"
                f"This code expires in {settings.LOGIN_CODE_EXPIRE_MINUTES} minutes."
            )
        db.add(user)
        db.commit()
        send_email(user.email, subject, body)

    return ForgotPasswordResponse(message="If the email exists, a code has been sent.")

@router.post("/reset")
@limiter.limit("10/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using a code sent via email.
    """
    user = crud_user.get_user_by_email(db, email=payload.email)
    if not user or not user.is_active or not user.reset_code_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset code")
    if not user.reset_code_expires_at or user.reset_code_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset code expired")
    if not verify_one_time_code(payload.code, user.reset_code_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset code")

    crud_user.update_user(
        db,
        db_user=user,
        user_in={
            "password": payload.new_password,
            "reset_code_hash": None,
            "reset_code_expires_at": None,
        },
    )
    return {"message": "Password reset successfully"}

@router.post("/login/code", response_model=Token)
@limiter.limit("10/minute")
def login_with_code(request: Request, payload: LoginCodeRequest, db: Session = Depends(get_db)):
    """
    Login with a one-time code sent via email.
    """
    user = crud_user.get_user_by_email(db, email=payload.email)
    if not user or not user.is_active or not user.login_code_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login code")
    if not user.login_code_expires_at or user.login_code_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login code expired")
    if not verify_one_time_code(payload.code, user.login_code_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login code")

    crud_user.update_user(
        db,
        db_user=user,
        user_in={
            "login_code_hash": None,
            "login_code_expires_at": None,
        },
    )
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")

@router.get("/github")
@limiter.limit("20/minute")
async def github_login(request: Request):
    """
    Redirect to GitHub OAuth login.
    """
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&scope=user:email"
    )

@router.get("/github/callback")
@limiter.limit("20/minute")
async def github_callback(request: Request, code: str, db: Session = Depends(get_db)):
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

        # Persist GitHub access token for repo access
        try:
            user.github_access_token = access_token
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as exc:
            logger.error("Failed to store GitHub token: %s", exc, exc_info=True)

        # Generate JWT and redirect to frontend callback
        access_token_jwt = create_access_token(data={"sub": str(user.id)})
        frontend = (settings.FRONTEND_BASE_URL or "http://localhost:3000").rstrip("/")
        redirect_url = (
            f"{frontend}/auth/github/callback"
            f"?token={access_token_jwt}&token_type=bearer"
        )
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    """
    Fetch the current logged in user.
    """
    return current_user

@router.patch("/me", response_model=User)
@limiter.limit("10/minute")
def update_users_me(
    request: Request,
    payload: UserNameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update current user's first name.
    """
    name = payload.full_name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="First name is required")
    user = crud_user.update_user(db, db_user=current_user, user_in={"full_name": name})
    return user
