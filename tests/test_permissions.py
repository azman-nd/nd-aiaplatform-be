import pytest
from fastapi import HTTPException, Request, status
from unittest.mock import MagicMock
from app.core.permissions import check_role_and_permission
import jwt
import os
import types
import asyncio

@pytest.mark.asyncio
async def test_check_role_and_permission_invalid_permission_format():
    """
    Test that check_role_and_permission raises HTTP 500 for invalid permission format
    """
    # Mock request with Authorization header
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": "Bearer mock_token"}

    # Mock current_user (not used for this test, but required)
    current_user = {"id": "test-user"}

    # Patch jwt.decode to return a valid payload
    def mock_jwt_decode(token, key, algorithms):
        return {
            "sub": "1234567890",
            "name": "Test User",
            "iat": 1516239022,
            "fea": "all_content",
            "o": {
                "rol": "admin",
                "per": "manage"
            }
        }

    # Patch os.getenv to return a dummy key
    os.environ["CLERK_JWT_KEY"] = "dummy_key"

    # Patch jwt.decode
    original_jwt_decode = jwt.decode
    jwt.decode = mock_jwt_decode

    try:
        with pytest.raises(HTTPException) as exc_info:
            await check_role_and_permission(
                mock_request,
                current_user,
                required_role="admin",
                required_permission="invalid_format"  # Not org:feature:action
            )
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Invalid permission format" in exc_info.value.detail
    finally:
        jwt.decode = original_jwt_decode 