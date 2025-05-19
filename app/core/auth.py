from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from clerk_backend_api.models import ClerkErrors, SDKError
import os
import jwt
from dotenv import load_dotenv
from functools import lru_cache
import time

load_dotenv()

CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
CLERK_JWT_KEY = os.getenv('CLERK_JWT_KEY')

security = HTTPBearer()

# Cache user information for 5 minutes
@lru_cache(maxsize=100)
def get_cached_user(user_id: str, timestamp: int):
    """
    Get user information from cache or Clerk API.
    Cache is invalidated every 5 minutes.
    """
    clerk = Clerk(bearer_auth=CLERK_SECRET_KEY)
    user = clerk.users.get(user_id=user_id)
    return {
        "id": user.id,
        "email": user.email_addresses[0].email_address if user.email_addresses else None,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate JWT token and return user information.
    Uses JWT payload directly and caches user information.
    """
    try:
        # jwt decode and signature verification
        payload = jwt.decode(
            credentials.credentials,
            CLERK_JWT_KEY,
            algorithms=["RS256"]
        )

        # Extract user information from JWT payload
        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail='Invalid token: No user ID found'
            )

        # Check if session is active
        session_id = payload.get('sid')
        if not session_id:
            raise HTTPException(
                status_code=401,
                detail='Invalid token: No session ID found'
            )

        # Get current timestamp for cache invalidation (5-minute intervals)
        current_timestamp = int(time.time() / 300)
        
        # Get user information from cache or Clerk API
        try:
            user_info = get_cached_user(user_id, current_timestamp)
        except (ClerkErrors, SDKError):
            # If cache miss or API error, try to get user directly
            clerk = Clerk(bearer_auth=CLERK_SECRET_KEY)
            user = clerk.users.get(user_id=user_id)
            user_info = {
                "id": user.id,
                "email": user.email_addresses[0].email_address if user.email_addresses else None,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            # Cache the user information
            get_cached_user.cache_clear()  # Clear old cache
            get_cached_user(user_id, current_timestamp)  # Cache new data

        return user_info

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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Authentication error: {str(e)}'
        ) 