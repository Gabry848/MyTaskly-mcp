"""Tests for authentication module."""

import pytest
from src.auth import create_test_token, verify_jwt_token
from fastapi import HTTPException


def test_create_test_token():
    """Test JWT token creation."""
    token = create_test_token(user_id=123, expires_minutes=30)
    assert isinstance(token, str)
    assert len(token) > 50  # JWT tokens are long


def test_verify_valid_token():
    """Test verification of valid JWT token."""
    user_id = 123
    token = create_test_token(user_id=user_id)
    auth_header = f"Bearer {token}"

    verified_user_id = verify_jwt_token(auth_header)
    assert verified_user_id == user_id


def test_verify_missing_token():
    """Test verification fails with missing token."""
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token(None)

    assert exc_info.value.status_code == 401
    assert "Missing Authorization header" in str(exc_info.value.detail)


def test_verify_invalid_format():
    """Test verification fails with invalid format."""
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token("InvalidFormat")

    assert exc_info.value.status_code == 401


def test_verify_expired_token():
    """Test verification fails with expired token."""
    # Create token that expires immediately
    token = create_test_token(user_id=123, expires_minutes=-1)
    auth_header = f"Bearer {token}"

    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token(auth_header)

    assert exc_info.value.status_code == 401
    assert "expired" in str(exc_info.value.detail).lower()
