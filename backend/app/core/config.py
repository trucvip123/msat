from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+aiomysql://msat:msatpassword@db/msatdb")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secure-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Email settings
    SMTP_TLS: bool = True  # Always use TLS for Gmail
    SMTP_PORT: int = 587  # Standard port for Gmail SMTP with STARTTLS
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")  # Use App Password for Gmail
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "MSAT Manager")
    
    # Password reset token expiration (in minutes)
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30"))
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 