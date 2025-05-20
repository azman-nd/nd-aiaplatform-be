from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import agents
import os
from dotenv import load_dotenv
from sqlalchemy import text
from app.core.database import engine
from app.core.auth import get_current_user
import logging
from contextlib import asynccontextmanager
from app.core.config import settings

load_dotenv()

CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
CLERK_JWT_KEY = os.getenv('CLERK_JWT_KEY')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger = logging.getLogger("uvicorn.error")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful on startup.")
    except Exception as e:
        logger.error(f"Database connection failed on startup: {e}")
    yield
    # Shutdown
    # Add any cleanup code here if needed

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for AI Agent Platform",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Important for cookies/auth
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to AI Agent Platform API"}

@app.get("/health")
async def health_check(current_user = Depends(get_current_user)):
    try:
        with engine.connect() as connection:
            # Get PostgreSQL version
            version_result = connection.execute(text("SELECT version()")).scalar()
            
            # Get current schema
            schema_result = connection.execute(text("SELECT current_schema()")).scalar()
            
            # Test connection with SELECT 1
            connection.execute(text("SELECT 1"))
            
            return {
                "app_status": "healthy",
                "db_status": "connected",
                "postgres_version": version_result,
                "current_schema": schema_result,
                "db_host": engine.url.host,
                "user": current_user["id"]  # Updated to use dictionary access since auth.py returns a dict
            }
    except Exception as e:
        return {"status": "unhealthy", "db": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
