from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.database import engine
from app.models.base import Base
from app.routers import auth
from app.core.config import settings
from app.core.logger import setup_logging
import time
import logging

# Setup logging
logger = setup_logging()

app = FastAPI(
    title="Msat Manager Backend",
    description="Backend API for MSAT Manager",
    version="1.0.0",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    logger.debug(f"Headers: {request.headers}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.2f}s")
        
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise

@app.on_event("startup")
async def startup():
    logger.info("Starting up application...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")

# Include routers
app.include_router(auth.router)
logger.info("Auth router included")

@app.get("/")
async def root():
    logger.debug("Root endpoint called")
    return {
        "message": "Welcome to Msat Manager API!",
        "version": "1.0.0",
        "docs_url": "/docs"
    } 