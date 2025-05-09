from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os
import time
from sqlalchemy.exc import OperationalError
import logging

logger = logging.getLogger(__name__)

# Only enable SQL echoing in development
echo = os.getenv("ENVIRONMENT", "production").lower() == "development"

def get_engine():
    return create_async_engine(
        settings.DATABASE_URL,
        echo=echo,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600
    )

engine = get_engine()
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            async with async_session() as session:
                try:
                    yield session
                finally:
                    await session.close()
            break
        except OperationalError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                raise
            logger.warning(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay) 