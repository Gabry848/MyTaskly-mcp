# 🚀 Quick Start Guide

Get the MyTaskly MCP Server running in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- MyTaskly FastAPI server running on `http://localhost:8080`
- JWT secret key from your FastAPI server

## Step 1: Install Dependencies

```bash
cd E:/MyTaskly/MyTaskly-mcp

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install packages
pip install fastmcp httpx pyjwt python-dotenv pydantic pydantic-settings
```

## Step 2: Configure Environment

1. Open `.env` file in the project root
2. Update `JWT_SECRET_KEY` to match your FastAPI server's secret key:

```env
JWT_SECRET_KEY=your_actual_jwt_secret_key_here
```

⚠️ **This MUST be the same secret key used by your FastAPI server!**

You can find it in your FastAPI server at:
- `E:/MyTaskly/MyTaskly-server/src/app/core/config.py`
- Look for `JWT_SECRET_KEY` or `SECRET_KEY`

## Step 3: Add MCP Token Endpoint to FastAPI

Add this endpoint to your FastAPI server to generate MCP tokens:

```python
# E:/MyTaskly/MyTaskly-server/src/app/api/routes/auth.py

from datetime import datetime, timedelta
import jwt
from src.app.core.config import settings

@router.post("/auth/mcp-token")
async def get_mcp_token(current_user: User = Depends(get_current_user)):
    """Generate JWT token for MCP server access."""
    payload = {
        "sub": str(current_user.user_id),
        "aud": "mcp://mytaskly-mcp-server",
        "iss": "https://api.mytasklyapp.com",
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow(),
        "scope": "tasks:read tasks:write categories:read notes:read notes:write"
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    return {"mcp_token": token, "expires_in": 1800}
```

## Step 4: Start the MCP Server

```bash
python -m src.server
```

You should see:
```
============================================================
🚀 Starting MyTaskly MCP Server v0.1.0
============================================================
FastAPI Backend: http://localhost:8080
...
```

## Step 5: Test It!

### Option A: Generate Test Token in Python

```bash
python -m tests.manual_test
```

Create `tests/manual_test.py`:
```python
import asyncio
from src.auth import create_test_token
from src.server import get_tasks, health_check

async def test():
    # Generate token for user_id=1
    token = create_test_token(user_id=1)
    print(f"✅ Generated token: {token[:50]}...")

    # Test health check (no auth)
    health = await health_check()
    print(f"✅ Health: {health}")

    # Test get_tasks (with auth)
    tasks = await get_tasks(authorization=f"Bearer {token}")
    print(f"✅ Tasks: {tasks['summary']}")
    print(f"   Voice: {tasks['voice_summary']}")

asyncio.run(test())
```

### Option B: Use Real Token from FastAPI

1. Login to your app and get access token:
```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

2. Get MCP token:
```bash
curl -X POST http://localhost:8080/auth/mcp-token \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

3. Test MCP server (replace YOUR_MCP_TOKEN):
```python
from src.server import get_tasks
import asyncio

async def test():
    token = "YOUR_MCP_TOKEN_HERE"
    tasks = await get_tasks(authorization=f"Bearer {token}")
    print(tasks)

asyncio.run(test())
```

## 🎉 Success!

If you see task data returned, your MCP server is working!

## Next Steps

1. **Integrate with chatbot** - See `README.md` for chatbot integration
2. **Add more tools** - Extend `src/server.py` with more MCP tools
3. **Deploy** - Deploy MCP server separately from FastAPI

## Troubleshooting

### "Invalid token signature"
- Check that `JWT_SECRET_KEY` matches your FastAPI server

### "FastAPI server unhealthy"
- Make sure your FastAPI server is running on `http://localhost:8080`
- Check `FASTAPI_BASE_URL` in `.env`

### "Module not found"
- Make sure you activated the virtual environment: `venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt`

## Need Help?

Check the full documentation in `README.md`
