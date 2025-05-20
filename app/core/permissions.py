from fastapi import HTTPException, status, Request, Depends
from typing import List, Optional, Set
import jwt
import os
import logging

logger = logging.getLogger(__name__)
CLERK_JWT_KEY = os.getenv('CLERK_JWT_KEY')

async def check_role_and_permission(request: Request, current_user: dict, required_role: str, required_permission: str):
    """
    Function to check if user has required role and permission.
    Gets role from o.rol and constructs permission as org:<fea>:<per>
    Handles comma-separated lists in fea and per fields.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        # Get the token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )

        token = auth_header.split(' ')[1]

        # Decode and verify the token
        payload = jwt.decode(
            token,
            CLERK_JWT_KEY,
            algorithms=["RS256"]
        )

        # Get organization data and feature from token claims
        org_data = payload.get('o', {})
        if not org_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organization data found in token"
            )

        # Check role first (fastest check)
        user_role = org_data.get('rol')
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {required_role}, Found: {user_role}"
            )

        # Parse required permission once
        try:
            _, required_feature, required_action = required_permission.split(':')
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid permission format: {required_permission}"
            )

        # Get features and permissions as sets for O(1) lookups
        features = {f.strip() for f in payload.get('fea', '').split(',') if f.strip()}
        permissions = {p.strip() for p in org_data.get('per', '').split(',') if p.strip()}

        if not features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No feature data found in token"
            )

        # Check if required feature and action are in the sets
        if required_feature in features and required_action in permissions:
            return True

        # If we get here, permission check failed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required_permission}. Found features: {features}, permissions: {permissions}"
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping them
        raise
    except Exception as e:
        logger.error(f"Unexpected error in permission check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking permissions: {str(e)}"
        ) 