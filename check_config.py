"""Quick script to check if .env is loaded correctly."""

from src.config import settings

print("=" * 60)
print("MCP Server Configuration Check")
print("=" * 60)
print(f"JWT_SECRET_KEY: {settings.jwt_secret_key[:20]}... (first 20 chars)")
print(f"JWT_ALGORITHM: {settings.jwt_algorithm}")
print(f"MCP_AUDIENCE: {settings.mcp_audience}")
print(f"FASTAPI_BASE_URL: {settings.fastapi_base_url}")
print(f"FASTAPI_API_KEY: {settings.fastapi_api_key}")
print("=" * 60)

# Also check if it matches expected value
expected_key = "349878uoti34h80943iotrhf-83490ewofridsh3t4iner"
if settings.jwt_secret_key == expected_key:
    print("✅ JWT_SECRET_KEY matches FastAPI server!")
else:
    print("❌ JWT_SECRET_KEY DOES NOT MATCH!")
    print(f"   Expected: {expected_key[:20]}...")
    print(f"   Got: {settings.jwt_secret_key[:20]}...")
