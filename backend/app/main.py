from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.models.base import Base
from app.routers import auth
from app.core.config import settings

app = FastAPI(
    title="Msat Manager Backend",
    description="Backend API for MSAT Manager",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Include routers
app.include_router(auth.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Msat Manager API!",
        "version": "1.0.0",
        "docs_url": "/docs"
    } 