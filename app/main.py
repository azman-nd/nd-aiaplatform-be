from clerk_backend_api import Clerk, ClerkErrors, SDKError
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.v1.endpoints import agents
import os
from dotenv import load_dotenv
import jwt
from sqlalchemy import text
from app.core.database import engine
import logging
from contextlib import asynccontextmanager

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
    title="AI Agent Platform",
    description="API for AI Agent Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Clerk client with the secret key
clerk_client = Clerk(bearer_auth=CLERK_SECRET_KEY)

# Dependency function to get the current authenticated user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    try:
        try:
            # jwt decode and signature verification
            payload = jwt.decode(
                credentials.credentials,
                CLERK_JWT_KEY,
                algorithms=["RS256"]
            )

            #extracting session_id from payload
            session_id = payload.get('sid')
            if not session_id:
                raise HTTPException(
                    status_code=401,
                    detail='Invalid token: No session ID found'
                )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail='Token has expired'
            )
        except jwt.InvalidSignatureError:
            raise HTTPException(
                status_code=401,
                detail='Invalid token signature'
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail='Invalid token format'
            )
        
        # Get session using the extracted session_id
        session = clerk_client.sessions.get(session_id=session_id)
        
        # Check if the session is active
        if not session or session.status != "active":
            raise HTTPException(
                status_code=401, 
                detail=f'Session is not active. Current status: {session.status if session else "no session"}'
            )
        
        # Get user details using the user_id from session
        user = clerk_client.users.get(user_id=session.user_id)
        
        if not user:
            raise HTTPException(
                status_code=401, 
                detail='No user found for session'
            )
        
        return user
    except ClerkErrors:
        raise HTTPException(status_code=401, detail='Invalid or expired session token')
    except SDKError:
        raise HTTPException(status_code=500, detail='Internal server error')

# Include routers
app.include_router(agents.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to AI Agent Platform API"}

@app.get("/health")
async def health_check():
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
                "db_host": engine.url.host
            }
    except Exception as e:
        return {"status": "unhealthy", "db": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
