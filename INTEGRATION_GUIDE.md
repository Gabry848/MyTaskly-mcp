# 🔗 Integration Guide - MCP Server with Voice Chat

This guide shows how to integrate the MCP server with your existing FastAPI voice chat system.

## Overview

```
User (Voice/Text) → FastAPI Chatbot → MCP Server → FastAPI API → Database
                         ↓                ↓
                    OpenAI GPT      Formatted Response
                         ↓                ↓
                    TTS/Text    ←   Voice + UI Data
```

## Step 1: Add MCP Token Endpoint to FastAPI

Add this to your FastAPI server to issue MCP tokens:

```python
# E:/MyTaskly/MyTaskly-server/src/app/api/routes/auth.py

from datetime import datetime, timedelta, timezone
import jwt
from src.app.core.config import settings

@router.post("/auth/mcp-token")
async def get_mcp_token(current_user: User = Depends(get_current_user)):
    """
    Generate JWT token specifically for MCP server access.

    This token has:
    - Audience claim for MCP server (RFC 8707)
    - Scopes for specific MCP operations
    - Short expiration (30 minutes)
    """
    payload = {
        "sub": str(current_user.user_id),
        "aud": "mcp://mytaskly-mcp-server",  # Resource Indicator
        "iss": "https://api.mytasklyapp.com",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "iat": datetime.now(timezone.utc),
        "scope": "tasks:read tasks:write categories:read notes:read notes:write"
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    return {
        "mcp_token": token,
        "expires_in": 1800,
        "token_type": "Bearer"
    }
```

## Step 2: Create MCP Client in Chatbot Service

Add MCP client to your chatbot service:

```python
# E:/MyTaskly/MyTaskly-server/src/app/services/mcp_client.py

import httpx
from typing import Dict, Any
from src.app.core.config import settings


class MCPClient:
    """Client for MyTaskly MCP Server."""

    def __init__(self, mcp_base_url: str = "http://localhost:8001"):
        self.base_url = mcp_base_url

    async def call_tool(
        self,
        tool_name: str,
        mcp_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call an MCP tool with authentication.

        Args:
            tool_name: Name of MCP tool (e.g., "get_tasks")
            mcp_token: JWT token for MCP authentication
            **kwargs: Additional parameters for the tool

        Returns:
            Tool response dictionary
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/mcp/{tool_name}",
                headers={
                    "Authorization": f"Bearer {mcp_token}",
                    "Content-Type": "application/json"
                },
                json=kwargs
            )
            response.raise_for_status()
            return response.json()

    async def get_tasks(self, mcp_token: str) -> Dict[str, Any]:
        """Get user tasks formatted for UI."""
        return await self.call_tool("get_tasks", mcp_token)

    async def get_categories(self, mcp_token: str) -> Dict[str, Any]:
        """Get user categories."""
        return await self.call_tool("get_categories", mcp_token)

    async def create_note(
        self,
        mcp_token: str,
        title: str,
        color: str = "#FFEB3B"
    ) -> Dict[str, Any]:
        """Create a new note."""
        return await self.call_tool(
            "create_note",
            mcp_token,
            title=title,
            color=color
        )


# Global instance
mcp_client = MCPClient(mcp_base_url=settings.MCP_SERVER_URL)
```

## Step 3: Update Chatbot Service to Use MCP

Modify your chatbot service to use MCP tools:

```python
# E:/MyTaskly/MyTaskly-server/src/app/services/chatbot_service.py

from src.app.services.mcp_client import mcp_client
from src.app.api.routes.auth import get_mcp_token  # Import the function


async def process_chat_message(
    user_id: int,
    message: str,
    is_voice: bool = False
) -> Dict[str, Any]:
    """
    Process chat message using OpenAI and MCP tools.
    """

    # 1. Generate MCP token for this user
    # In production, cache this token until it expires
    from src.app.models.user import User
    user = await User.get(user_id=user_id)

    # Create a mock "current_user" for get_mcp_token
    # Or better: extract the token generation logic to a separate function
    mcp_token_data = await generate_mcp_token_for_user(user_id)
    mcp_token = mcp_token_data["mcp_token"]

    # 2. Define MCP tools for OpenAI function calling
    mcp_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_tasks",
                "description": "Get all tasks for the user, formatted for React Native UI",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_categories",
                "description": "Get all categories for the user",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_note",
                "description": "Create a quick note/reminder",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Note text content"
                        },
                        "color": {
                            "type": "string",
                            "description": "Hex color code",
                            "default": "#FFEB3B"
                        }
                    },
                    "required": ["title"]
                }
            }
        }
    ]

    # 3. Call OpenAI with MCP tools
    openai_response = await openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": get_system_prompt(is_voice)},
            {"role": "user", "content": message}
        ],
        tools=mcp_tools,
        tool_choice="auto"
    )

    # 4. Handle tool calls
    response_message = openai_response.choices[0].message

    if response_message.tool_calls:
        # Execute MCP tool
        tool_call = response_message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        # Call MCP server
        if tool_name == "get_tasks":
            mcp_result = await mcp_client.get_tasks(mcp_token)
        elif tool_name == "get_categories":
            mcp_result = await mcp_client.get_categories(mcp_token)
        elif tool_name == "create_note":
            mcp_result = await mcp_client.create_note(
                mcp_token,
                title=tool_args["title"],
                color=tool_args.get("color", "#FFEB3B")
            )

        # 5. Format response based on mode
        if is_voice:
            # Voice mode: return voice_summary
            return {
                "text": mcp_result.get("voice_summary", "Operazione completata"),
                "ui_data": mcp_result,  # Send UI data to client anyway
                "type": "mcp_response"
            }
        else:
            # Text mode: return formatted UI data
            return {
                "text": f"Ecco i tuoi dati:",
                "ui_data": mcp_result,
                "type": "mcp_response"
            }

    # No tool calls - regular chat response
    return {
        "text": response_message.content,
        "type": "text_response"
    }


async def generate_mcp_token_for_user(user_id: int) -> Dict[str, str]:
    """Generate MCP token for a specific user ID."""
    payload = {
        "sub": str(user_id),
        "aud": "mcp://mytaskly-mcp-server",
        "iss": "https://api.mytasklyapp.com",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "iat": datetime.now(timezone.utc),
        "scope": "tasks:read tasks:write categories:read notes:read notes:write"
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    return {
        "mcp_token": token,
        "expires_in": 1800
    }
```

## Step 4: Update System Prompts

Update your chatbot system prompts to mention MCP capabilities:

```python
# E:/MyTaskly/MyTaskly-server/src/prompts/chatbot_system_prompts.md

## FUNZIONI DISPONIBILI (MCP):

Hai accesso a queste funzioni via MCP:

- **get_tasks**: Ottiene tutti i task dell'utente formattati per UI mobile
  - Restituisce dati ottimizzati per React Native
  - Include voice_summary per modalità vocale
  - Usa questa funzione quando l'utente chiede "mostrami i task", "cosa devo fare", ecc.

- **get_categories**: Ottiene tutte le categorie dell'utente
  - Usa quando l'utente chiede "quali categorie ho", "come sono organizzati i task"

- **create_note**: Crea una nota rapida
  - Usa per appunti veloci, idee, promemoria semplici
  - Supporta colori personalizzati

IMPORTANTE:
- Per modalità VOCALE: usa sempre voice_summary nella risposta
- Per modalità TESTO: descrivi i dati ritornati in modo chiaro
```

## Step 5: Client Integration (React Native)

Client-side handling of MCP responses:

```tsx
// Mobile App - Chat Screen

interface MCPResponse {
  text: string;
  ui_data?: any;
  type: 'mcp_response' | 'text_response';
}

async function sendMessage(message: string, isVoice: boolean) {
  const response = await fetch('http://localhost:8080/chatbot/chat', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      is_voice: isVoice
    })
  });

  const data: MCPResponse = await response.json();

  if (data.type === 'mcp_response' && data.ui_data) {
    // Check if it's task data
    if (data.ui_data.type === 'task_list') {
      // Show tasks UI
      navigation.navigate('TasksList', { data: data.ui_data });

      // If voice mode, also play TTS
      if (isVoice && data.ui_data.voice_summary) {
        await playTTS(data.ui_data.voice_summary);
      }
    }
  } else {
    // Regular text/voice response
    if (isVoice) {
      await playTTS(data.text);
    } else {
      showChatMessage(data.text);
    }
  }
}
```

## Step 6: Environment Configuration

Add to your FastAPI `.env`:

```env
# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8001

# JWT Secret (MUST be the same for both servers!)
JWT_SECRET_KEY=your_shared_secret_key_here
```

## Step 7: Deployment

### Development (local)

Terminal 1:
```bash
# FastAPI Server
cd E:/MyTaskly/MyTaskly-server
uvicorn main:app --reload --port 8080
```

Terminal 2:
```bash
# MCP Server
cd E:/MyTaskly/MyTaskly-mcp
python -m src.server
```

### Production (separate deployments)

1. **FastAPI Server**: Deploy to Railway/Heroku (existing)
   - URL: `https://api.mytasklyapp.com`

2. **MCP Server**: Deploy separately
   - URL: `https://mcp.mytasklyapp.com`
   - Update `MCP_SERVER_URL` in FastAPI env vars

## Example: Voice Chat Flow

```
User (Voice): "Mostrami i miei task"
    ↓
FastAPI Chatbot receives transcription
    ↓
Generates MCP token for user
    ↓
OpenAI decides to call get_tasks tool
    ↓
FastAPI calls MCP Server with token
    ↓
MCP Server validates JWT, calls FastAPI /tasks endpoint
    ↓
MCP Server formats response for React Native
    ↓
FastAPI receives formatted response
    ↓
FastAPI sends to client:
  {
    "text": "Hai 10 task, 2 ad alta priorità",  // For TTS
    "ui_data": {                                // For UI
      "type": "task_list",
      "tasks": [...],
      "voice_summary": "Hai 10 task..."
    }
  }
    ↓
Mobile App:
  - Plays TTS: "Hai 10 task, 2 ad alta priorità"
  - Shows TasksList UI with formatted data
```

## Security Checklist

- ✅ JWT secret is shared between FastAPI and MCP
- ✅ MCP tokens have short expiration (30 min)
- ✅ MCP tokens have specific audience claim
- ✅ MCP server validates audience in JWT
- ✅ HTTPS in production
- ✅ MCP server doesn't have database access
- ✅ All data flows through authenticated FastAPI endpoints

## Testing the Integration

```python
# Test script
import requests

# 1. Login to FastAPI
login_response = requests.post(
    'http://localhost:8080/auth/login',
    json={'username': 'test', 'password': 'test'}
)
access_token = login_response.json()['access_token']

# 2. Get MCP token
mcp_response = requests.post(
    'http://localhost:8080/auth/mcp-token',
    headers={'Authorization': f'Bearer {access_token}'}
)
mcp_token = mcp_response.json()['mcp_token']

# 3. Test MCP server directly
tasks_response = requests.post(
    'http://localhost:8001/mcp/get_tasks',
    headers={'Authorization': f'Bearer {mcp_token}'}
)
print(tasks_response.json())
```

Done! Your MCP server is now integrated with your voice chat system. 🎉
