# MyTaskly MCP Server

MCP (Model Context Protocol) server for MyTaskly with **OAuth 2.1 authentication** and HTTP API integration.

## 🌟 Features

- ✅ **OAuth 2.1 JWT Authentication** - Secure token-based authentication following MCP 2025 standards
- ✅ **Multi-User Support** - Single deployment serves all users via JWT token validation
- ✅ **HTTP API Integration** - Communicates with FastAPI backend, no direct database access
- ✅ **React Native Optimized** - Returns data formatted for native mobile components
- ✅ **Voice-Friendly** - Includes voice summaries for TTS in chat applications
- ✅ **Stateless** - No session management, fully scalable

## 📋 Available Tools

### 1. `get_tasks`
Get all tasks for authenticated user, formatted for React Native UI components.

**Authentication:** Required (JWT Bearer token)

**Returns:**
```json
{
  "type": "task_list",
  "tasks": [
    {
      "id": 123,
      "title": "Pizza",
      "endTimeFormatted": "Venerdì 15 dicembre, 18:00",
      "category": "Cibo",
      "categoryColor": "#EF4444",
      "priority": "Alta",
      "priorityEmoji": "⚡",
      "actions": {...}
    }
  ],
  "summary": {
    "total": 10,
    "pending": 5,
    "high_priority": 2
  },
  "voice_summary": "Hai 10 task, di cui 2 ad alta priorità..."
}
```

### 2. `get_categories`
Get all categories for authenticated user.

**Authentication:** Required (JWT Bearer token)

**Returns:**
```json
{
  "categories": [
    {
      "category_id": 1,
      "name": "Lavoro",
      "description": "Task di lavoro"
    }
  ],
  "total": 5
}
```

### 3. `create_note`
Create a new note (post-it style).

**Authentication:** Required (JWT Bearer token)

**Parameters:**
- `title` (required): Note text content
- `position_x` (optional): X position on canvas
- `position_y` (optional): Y position on canvas
- `color` (optional): Hex color code (default: "#FFEB3B")

**Returns:**
```json
{
  "note_id": 456,
  "title": "Comprare il latte",
  "color": "#FFEB3B",
  "message": "✅ Nota creata con successo"
}
```

### 4. `health_check`
Check server health status.

**Authentication:** Not required

**Returns:**
```json
{
  "mcp_server": "healthy",
  "fastapi_server": "healthy",
  "fastapi_url": "http://localhost:8080"
}
```

## 🚀 Setup

### 1. Install Dependencies

```bash
cd E:/MyTaskly/MyTaskly-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -e .
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# FastAPI Server
FASTAPI_BASE_URL=http://localhost:8080
FASTAPI_API_KEY=your_api_key_here

# JWT Configuration (MUST match FastAPI server!)
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
MCP_AUDIENCE=mcp://mytaskly-mcp-server
```

⚠️ **IMPORTANT:** `JWT_SECRET_KEY` MUST be the same as your FastAPI server's secret key!

### 3. Run the Server

```bash
python -m src.server
```

You should see:
```
============================================================
🚀 Starting MyTaskly MCP Server v0.1.0
============================================================
FastAPI Backend: http://localhost:8080
JWT Audience: mcp://mytaskly-mcp-server
============================================================

📋 Available Tools:
  1. get_tasks - Get all user tasks (formatted for React Native)
  2. get_categories - Get user categories
  3. create_note - Create a new note
  4. health_check - Check server health (no auth required)

🔐 Authentication: OAuth 2.1 JWT (Bearer token)
============================================================
```

## 🔐 Authentication Flow

### How it works:

1. **User logs in** → FastAPI server (`POST /auth/login`)
2. **FastAPI generates JWT** with MCP audience claim
3. **Client receives JWT** and stores it
4. **Client calls MCP tools** passing JWT in `Authorization` header
5. **MCP validates JWT** and executes tool for authenticated user

### JWT Token Format

The JWT must include these claims:

```json
{
  "sub": "123",                              // User ID (required)
  "aud": "mcp://mytaskly-mcp-server",       // Audience (required, RFC 8707)
  "iss": "https://api.mytasklyapp.com",     // Issuer (optional)
  "exp": 1735689600,                         // Expiration (required)
  "iat": 1735686000,                         // Issued at (required)
  "scope": "tasks:read tasks:write ..."     // Scopes (optional)
}
```

### Getting a JWT Token

**Option 1: From FastAPI (Production)**

You need to add this endpoint to your FastAPI server:

```python
# src/app/api/routes/auth.py

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

**Option 2: Generate Test Token (Development)**

```python
from src.auth import create_test_token

# Generate test token for user_id=1
token = create_test_token(user_id=1, expires_minutes=30)
print(f"Test Token: {token}")
```

## 🧪 Testing

### Test with Python

```python
import asyncio
from src.auth import create_test_token
from src.server import get_tasks, get_categories, create_note

async def test_mcp():
    # Generate test token for user_id=1
    token = create_test_token(user_id=1)
    auth_header = f"Bearer {token}"

    # Test get_tasks
    print("Testing get_tasks...")
    tasks = await get_tasks(authorization=auth_header)
    print(f"✅ Got {tasks['summary']['total']} tasks")
    print(f"Voice: {tasks['voice_summary']}")

    # Test get_categories
    print("\nTesting get_categories...")
    categories = await get_categories(authorization=auth_header)
    print(f"✅ Got {categories['total']} categories")

    # Test create_note
    print("\nTesting create_note...")
    note = await create_note(
        authorization=auth_header,
        title="Test note from MCP",
        color="#4CAF50"
    )
    print(f"✅ Created note: {note['title']}")

# Run test
asyncio.run(test_mcp())
```

### Test with curl

```bash
# First, generate a test token
python -c "from src.auth import create_test_token; print(create_test_token(1))"

# Use the token in requests
curl -X POST http://localhost:8000/mcp/get_tasks \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📱 Integration with React Native

The `get_tasks` tool returns data optimized for React Native components:

```tsx
import { FlatList, View, Text } from 'react-native';

async function fetchTasks() {
  // Get JWT token from your auth system
  const token = await getAuthToken();

  // Call MCP server
  const response = await mcpClient.call('get_tasks', {
    authorization: `Bearer ${token}`
  });

  return response;
}

function TasksList() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchTasks().then(setData);
  }, []);

  if (!data) return <Loading />;

  return (
    <View>
      {/* Voice summary for accessibility */}
      <Text accessible>{data.voice_summary}</Text>

      {/* Render tasks list */}
      <FlatList
        data={data.tasks}
        renderItem={({ item }) => (
          <TaskCard
            title={item.title}
            date={item.endTimeFormatted}
            category={item.category}
            categoryColor={item.categoryColor}
            priority={item.priorityEmoji}
          />
        )}
      />
    </View>
  );
}
```

## 🎤 Integration with Voice Chat

The response includes `voice_summary` for TTS:

```python
# In your chatbot service
response = await mcp_client.call('get_tasks', {
    'authorization': f'Bearer {user_jwt}'
})

# For visual display
ui_data = response['tasks']

# For voice output
tts_text = response['voice_summary']
# "Hai 10 task, di cui 2 ad alta priorità. 5 sono in sospeso e 3 completati."
```

## 🔒 Security Best Practices

1. **Always use HTTPS** in production
2. **Keep JWT_SECRET_KEY secure** - never commit to git
3. **Use short-lived tokens** (15-30 minutes)
4. **Implement token refresh** in your client
5. **Validate audience claim** (RFC 8707) - prevents token reuse
6. **Log authentication failures** for monitoring

## 🏗️ Architecture

```
┌─────────────────┐
│  Mobile Client  │
│  (React Native) │
└────────┬────────┘
         │ 1. Login
         ▼
┌─────────────────┐
│  FastAPI Server │ 2. Issues JWT with MCP audience
│  (Auth Server)  │
└────────┬────────┘
         │ 3. Returns JWT
         ▼
┌─────────────────┐
│  Mobile Client  │ 4. Calls MCP tools with JWT
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP Server    │ 5. Validates JWT
│ (This project)  │ 6. Extracts user_id
└────────┬────────┘
         │ 7. Makes HTTP request with user_id
         ▼
┌─────────────────┐
│  FastAPI Server │ 8. Returns user data
│ (Resource API)  │
└────────┬────────┘
         │ 9. Formats for mobile
         ▼
┌─────────────────┐
│   MCP Server    │ 10. Returns formatted response
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Mobile Client  │ 11. Renders UI / plays TTS
└─────────────────┘
```

## 📚 Next Steps

To integrate with your FastAPI server:

1. **Add MCP token endpoint** to FastAPI (see example above)
2. **Test authentication** with generated token
3. **Integrate with chatbot** service for voice support
4. **Add more MCP tools** as needed (update_task, delete_task, etc.)

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black src/

# Lint code
ruff check src/

# Run tests
pytest tests/
```

## 📄 License

MIT

## 🤝 Contributing

This is part of the MyTaskly project. For issues or questions, please contact the development team.
