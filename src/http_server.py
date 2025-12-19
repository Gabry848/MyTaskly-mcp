"""HTTP Server wrapper for MCP Server to expose tools as HTTP endpoints."""

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

from src.auth import verify_jwt_token
from src.server import get_tasks, get_categories, create_note, health_check
from src.config import settings


# ===== LIFESPAN EVENTS =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("=" * 70)
    print(f"[*] {settings.mcp_server_name} v{settings.mcp_server_version}")
    print("=" * 70)
    print(f"[+] Server running on: http://0.0.0.0:8000")
    print(f"[+] API Documentation: http://localhost:8000/docs")
    print(f"[+] FastAPI Backend: {settings.fastapi_base_url}")
    print(f"[+] Authentication: OAuth 2.1 JWT (Bearer token)")
    print("=" * 70)
    print("\n[+] Available MCP Tools:")
    print("  POST /mcp/get_tasks      - Get user tasks (React Native optimized)")
    print("  POST /mcp/get_categories - Get user categories")
    print("  POST /mcp/create_note    - Create a new note")
    print("  GET  /health             - Health check (no auth)")
    print("=" * 70)

    yield

    # Shutdown
    print("\n" + "=" * 70)
    print("[!] MCP Server shutting down...")
    print("=" * 70)


# Create FastAPI app
app = FastAPI(
    title=settings.mcp_server_name,
    version=settings.mcp_server_version,
    description="HTTP API wrapper for MyTaskly MCP Server with OAuth 2.1 authentication",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== REQUEST/RESPONSE MODELS =====

class CreateNoteRequest(BaseModel):
    """Request model for creating a note."""
    title: str
    position_x: str = "0"
    position_y: str = "0"
    color: str = "#FFEB3B"


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None


# ===== HEALTH CHECK =====

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with server information."""
    return {
        "server": settings.mcp_server_name,
        "version": settings.mcp_server_version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "mcp_tools": {
                "get_tasks": "POST /mcp/get_tasks",
                "get_categories": "POST /mcp/get_categories",
                "create_note": "POST /mcp/create_note"
            }
        }
    }


@app.get("/health", tags=["Health"])
async def health():
    """
    Health check endpoint (no authentication required).

    Returns status of both MCP server and FastAPI backend.
    """
    return await health_check()


# ===== MCP TOOL ENDPOINTS =====

@app.post("/mcp/get_tasks", tags=["MCP Tools"])
async def http_get_tasks(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get all tasks for authenticated user.

    Returns tasks formatted for React Native UI components with:
    - Column definitions
    - Formatted task data (dates, colors, emojis)
    - Summary statistics
    - Voice summary for TTS
    - UI hints for rendering

    **Authentication Required**: Bearer JWT token

    **Example Request**:
    ```bash
    curl -X POST http://localhost:8000/mcp/get_tasks \
      -H "Authorization: Bearer YOUR_JWT_TOKEN"
    ```

    **Example Response**:
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
          "priorityEmoji": "[!]",
          "actions": {...}
        }
      ],
      "summary": {"total": 10, "high_priority": 2},
      "voice_summary": "Hai 10 task, di cui 2 ad alta priorità..."
    }
    ```
    """
    return await get_tasks(authorization=authorization)


@app.post("/mcp/get_categories", tags=["MCP Tools"])
async def http_get_categories(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get all categories for authenticated user.

    **Authentication Required**: Bearer JWT token

    **Example Request**:
    ```bash
    curl -X POST http://localhost:8000/mcp/get_categories \
      -H "Authorization: Bearer YOUR_JWT_TOKEN"
    ```

    **Example Response**:
    ```json
    {
      "categories": [
        {
          "category_id": 1,
          "name": "Lavoro",
          "description": "Task di lavoro",
          "user_id": 123
        }
      ],
      "total": 5
    }
    ```
    """
    return await get_categories(authorization=authorization)


@app.post("/mcp/create_note", tags=["MCP Tools"])
async def http_create_note(
    request: CreateNoteRequest,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Create a new note for authenticated user.

    **Authentication Required**: Bearer JWT token

    **Request Body**:
    ```json
    {
      "title": "Comprare il latte",
      "color": "#FFEB3B"
    }
    ```

    **Example Request**:
    ```bash
    curl -X POST http://localhost:8000/mcp/create_note \
      -H "Authorization: Bearer YOUR_JWT_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"title": "Test note", "color": "#4CAF50"}'
    ```

    **Example Response**:
    ```json
    {
      "note_id": 456,
      "title": "Comprare il latte",
      "color": "#FFEB3B",
      "message": "[OK] Nota creata con successo"
    }
    ```
    """
    return await create_note(
        authorization=authorization,
        title=request.title,
        position_x=request.position_x,
        position_y=request.position_y,
        color=request.color
    )


# ===== ERROR HANDLERS =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": f"HTTP_{exc.status_code}"
        },
        headers=exc.headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    from fastapi.responses import JSONResponse
    import traceback
    print(f"[ERROR] Unexpected error: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "error_code": "INTERNAL_ERROR"
        }
    )


# ===== MAIN =====

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the HTTP server.

    Args:
        host: Host to bind to (default: 0.0.0.0 for all interfaces)
        port: Port to listen on (default: 8000)
    """
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run_server()
