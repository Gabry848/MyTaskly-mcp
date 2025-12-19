# ✅ Installation Checklist

Follow these steps to get your MCP server running:

## Prerequisites
- [ ] Python 3.10+ installed
- [ ] MyTaskly FastAPI server running
- [ ] Access to FastAPI server's JWT_SECRET_KEY

## Installation Steps

### 1. Quick Install (Recommended)
```bash
# Windows
install.bat

# Linux/Mac
chmod +x install.sh
./install.sh
```

### 2. Manual Install
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### 3. Configure Environment
- [ ] Copy `.env.example` to `.env` (if not done automatically)
- [ ] Open `.env` in a text editor
- [ ] Set `JWT_SECRET_KEY` to match your FastAPI server
  - Find it in: `E:/MyTaskly/MyTaskly-server/src/app/core/config.py`
  - Variable name: `JWT_SECRET_KEY` or `SECRET_KEY`
  - Example: `JWT_SECRET_KEY=abc123xyz789`

### 4. Verify Configuration
```bash
python -c "from src.config import settings; print(settings.jwt_secret_key)"
```

Should print your JWT secret key (not "your_jwt_secret_key_here")

## FastAPI Server Setup

### 5. Add MCP Token Endpoint
Add this to `E:/MyTaskly/MyTaskly-server/src/app/api/routes/auth.py`:

```python
from datetime import datetime, timedelta, timezone
import jwt

@router.post("/auth/mcp-token")
async def get_mcp_token(current_user: User = Depends(get_current_user)):
    """Generate JWT token for MCP server access."""
    payload = {
        "sub": str(current_user.user_id),
        "aud": "mcp://mytaskly-mcp-server",
        "iss": "https://api.mytasklyapp.com",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "iat": datetime.now(timezone.utc),
        "scope": "tasks:read tasks:write categories:read notes:read notes:write"
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    return {"mcp_token": token, "expires_in": 1800}
```

## Testing

### 6. Start MCP Server
```bash
python -m src.server
```

Expected output:
```
============================================================
🚀 Starting MyTaskly MCP Server v0.1.0
============================================================
FastAPI Backend: http://localhost:8080
...
```

### 7. Run Tests
In a new terminal (keep server running):
```bash
# Activate venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run tests
python -m tests.manual_test
```

Expected output:
```
✅ MCP Server: healthy
✅ FastAPI Server: healthy
✅ Token generated: ...
✅ Total tasks: X
...
```

## Troubleshooting

### "Invalid token signature"
- [ ] JWT_SECRET_KEY doesn't match FastAPI server
- [ ] Check both `.env` files have same secret

### "FastAPI server unhealthy"
- [ ] FastAPI server is not running
- [ ] Check FASTAPI_BASE_URL in `.env`
- [ ] Try: `curl http://localhost:8080/health`

### "Module not found"
- [ ] Virtual environment not activated
- [ ] Dependencies not installed
- [ ] Try: `pip install -r requirements.txt`

### "Connection refused"
- [ ] Check FastAPI server is running on port 8080
- [ ] Check firewall settings
- [ ] Try: `netstat -an | findstr 8080`

## Next Steps

Once tests pass:
- [ ] Read `INTEGRATION_GUIDE.md` for chatbot integration
- [ ] Test with real user tokens
- [ ] Deploy to production

## Support

- Documentation: `README.md`
- Quick start: `QUICKSTART.md`
- Integration: `INTEGRATION_GUIDE.md`
- Project info: `PROJECT_SUMMARY.md`
