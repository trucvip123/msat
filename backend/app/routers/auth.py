from fastapi import APIRouter, Depends, HTTPException, status, Header, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, Token, PasswordChange,
    PasswordResetRequest, PasswordReset
)
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.core.config import settings
from sqlalchemy.future import select
import re
from datetime import datetime, timedelta
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.email_service import send_email
from sqlalchemy import update
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def validate_password(password: str) -> bool:
    """Validate password complexity"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

async def get_user(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_reset_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    if not validate_password(user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
        )
    
    db_user = await get_user(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = pwd_context.hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token({"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await get_user(db, user.username)
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token({"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except (JWTError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = await get_user(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify current password
    if not pwd_context.verify(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if not validate_password(password_change.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
        )
    
    # Hash and update new password
    current_user.hashed_password = pwd_context.hash(password_change.new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/request-password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    fastapi_request: Request = None
):
    logger.info(f"Password reset requested for email: {request.email}")
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()
    
    if not user:
        logger.warning(f"Password reset attempted for non-existent email: {request.email}")
        # Don't reveal that the email doesn't exist
        return {"message": "None existent email!"}
    
    # Create reset token
    reset_token = create_reset_token({"sub": user.email})
    logger.debug(f"Reset token created for user: {user.username}")
    
    # Get current base URL (e.g., http://your-domain.com)
    base_url = str(fastapi_request.base_url).rstrip("/")
    
    # Create reset URL (in production, replace with your frontend URL)
    reset_url = f"{base_url}/auth/reset-password?token={reset_token}"
    print("reset_url:", reset_url)
    
    try:
        # Send email
        await send_email(
            email_to=user.email,
            subject="Reset Your Password",
            template_name="reset_password",
            template_data={
                "reset_url": reset_url,
                "expiration_minutes": settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            }
        )
        logger.info(f"Reset password email sent to: {user.email}")
    except Exception as e:
        logger.error(f"Failed to send reset password email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset password email"
        )
    
    return {"message": "If your email is registered, you will receive a password reset link"}

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_form(token: str):
    # Return an HTML form that includes the token and lets the user enter new password
    return f"""
    <html>
        <head><title>Reset Password</title></head>
        <body>
            <h2>Reset Your Password</h2>
            <form action="/auth/reset-password" method="post">
                <input type="hidden" name="token" value="{token}" />
                <input type="password" name="new_password" placeholder="New Password" required />
                <button type="submit">Reset Password</button>
            </form>
        </body>
    </html>
    """


@router.post("/reset-password")
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    logger.info("Password reset attempt with token")
    
    try:
        # Verify token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Invalid reset token: missing email")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
    except JWTError as e:
        logger.warning(f"Invalid or expired reset token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user:
        logger.warning(f"Password reset attempted for non-existent user with email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate new password
    if not validate_password(new_password):
        logger.warning(f"Invalid password format for user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
        )
    
    # Update password
    user.hashed_password = pwd_context.hash(new_password)
    await db.commit()
    logger.info(f"Password successfully reset for user: {user.username}")
    
    return {"message": "Password has been reset successfully"} 