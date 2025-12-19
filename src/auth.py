"""OAuth 2.1 JWT authentication middleware for MCP Server."""

import jwt
from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException, Header
from src.config import settings


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


def verify_jwt_token(authorization: Optional[str] = Header(None)) -> int:
    """
    Verify JWT token and extract user_id.

    This implements OAuth 2.1 Resource Server token validation.
    The MCP server acts as a Resource Server, validating tokens
    issued by the FastAPI Authorization Server.

    Args:
        authorization: Authorization header with format "Bearer <token>"

    Returns:
        user_id: Integer user ID extracted from token

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": 'Bearer realm="MCP"'}
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": 'Bearer realm="MCP"'}
        )

    token = authorization.replace("Bearer ", "").strip()

    try:
        # Decode and validate JWT
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.mcp_audience,  # Resource Indicator validation (RFC 8707)
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "require": ["sub", "aud", "exp", "iat"]
            }
        )

        # Extract user_id from "sub" claim
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Token missing 'sub' claim")

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise AuthenticationError(f"Invalid 'sub' claim format: {user_id_str}")

        # Optional: Validate issuer if configured
        if "iss" in payload:
            expected_issuer = "https://api.mytasklyapp.com"
            if payload["iss"] != expected_issuer:
                raise AuthenticationError(f"Invalid issuer: {payload['iss']}")

        # Optional: Log successful authentication
        print(f"OK Authenticated user_id={user_id} with token scope: {payload.get('scope', 'N/A')}")

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Token expired"'}
        )

    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token audience. Expected: {settings.mcp_audience}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Invalid audience"'}
        )

    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Invalid signature"'}
        )

    except jwt.DecodeError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token decode error: {str(e)}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Malformed token"'}
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'}
        )

    except Exception as e:
        print(f"ERROR Unexpected authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'}
        )


def create_test_token(user_id: int, expires_minutes: int = 30) -> str:
    """
    Create a test JWT token for development/testing.

    In production, tokens should ONLY be created by the FastAPI Authorization Server.
    This function is for testing the MCP server independently.

    Args:
        user_id: User ID to encode in token
        expires_minutes: Token expiration time in minutes

    Returns:
        JWT token string
    """
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "aud": settings.mcp_audience,
        "iss": "https://api.mytasklyapp.com",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "scope": "tasks:read tasks:write categories:read categories:write notes:read notes:write"
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token
