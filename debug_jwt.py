"""Debug JWT token generation and validation."""

import jwt
from datetime import datetime, timedelta, timezone
from src.config import settings

print("=" * 60)
print("JWT Token Debug")
print("=" * 60)

# Check settings
print(f"\nMCP Server Settings:")
print(f"  JWT_SECRET_KEY: {settings.jwt_secret_key[:30]}...")
print(f"  JWT_ALGORITHM: {settings.jwt_algorithm}")
print(f"  MCP_AUDIENCE: {settings.mcp_audience}")

# Generate a test token (same as external_mcp_client.py does)
user_id = 1
now = datetime.now(timezone.utc)
expires_minutes = 30

payload = {
    "sub": str(user_id),
    "aud": "mcp://mytaskly-mcp-server",
    "iss": "https://api.mytasklyapp.com",
    "iat": int(now.timestamp()),
    "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    "scope": "tasks:read tasks:write categories:read categories:write notes:read notes:write"
}

print(f"\nToken Payload:")
print(f"  sub: {payload['sub']}")
print(f"  aud: {payload['aud']}")
print(f"  iss: {payload['iss']}")
print(f"  iat: {payload['iat']}")
print(f"  exp: {payload['exp']}")
print(f"  scope: {payload['scope']}")

# Generate token
token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
print(f"\nGenerated Token:")
print(f"  {token[:80]}...")

# Try to decode it
print(f"\nValidating Token...")
try:
    decoded = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=settings.mcp_audience,
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": True,
            "require": ["sub", "aud", "exp", "iat"]
        }
    )
    print("SUCCESS: Token is valid!")
    print(f"\nDecoded Payload:")
    print(f"  sub: {decoded['sub']}")
    print(f"  aud: {decoded['aud']}")
    print(f"  iss: {decoded.get('iss', 'N/A')}")

except jwt.ExpiredSignatureError:
    print("ERROR: Token has expired")
except jwt.InvalidAudienceError as e:
    print(f"ERROR: Invalid audience - {e}")
except jwt.InvalidSignatureError as e:
    print(f"ERROR: Invalid signature - {e}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
