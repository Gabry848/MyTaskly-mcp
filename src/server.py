"""MyTaskly MCP Server with OAuth 2.1 authentication."""

from fastmcp import FastMCP
from typing import Dict, Any, List
from src.auth import verify_jwt_token
from src.client import fastapi_client
from src.formatters import format_tasks_for_ui
from src.config import settings

# Create MCP server instance
mcp = FastMCP(
    name=settings.mcp_server_name,
    version=settings.mcp_server_version,
    instructions="MCP server for MyTaskly with OAuth 2.1 authentication and HTTP API integration"
)


# ===== AUTHENTICATION DEPENDENCY =====

async def get_authenticated_user_id(authorization: str) -> int:
    """
    Extract and validate user_id from JWT token.

    This dependency is used by all MCP tools to ensure authentication.
    """
    return verify_jwt_token(authorization)


# ===== MCP TOOLS =====

async def get_tasks(authorization: str) -> Dict[str, Any]:
    """
    Get all tasks for the authenticated user.

    Returns tasks in a format optimized for React Native components with:
    - Formatted data ready for mobile UI
    - Column definitions for table/list rendering
    - Summary statistics (total, pending, completed, high priority)
    - Voice summary for TTS
    - UI hints for display mode and interactions

    Authentication:
        Requires valid JWT token in Authorization header: "Bearer <token>"

    Returns:
        {
            "type": "task_list",
            "version": "1.0",
            "columns": [...],  # Column definitions for rendering
            "tasks": [         # Array of formatted task objects
                {
                    "id": 123,
                    "title": "Pizza",
                    "description": "...",
                    "endTime": "2025-12-15T18:00:00",
                    "endTimeFormatted": "Venerdì 15 dicembre, 18:00",
                    "category": "Cibo",
                    "categoryColor": "#EF4444",
                    "priority": "Alta",
                    "priorityEmoji": "[!]",
                    "priorityColor": "#EF4444",
                    "status": "In sospeso",
                    "actions": {
                        "complete": {"label": "[OK] Completa", "enabled": true},
                        "edit": {"label": "✏️ Modifica", "enabled": true},
                        "delete": {"label": "🗑️ Elimina", "enabled": true}
                    }
                }
            ],
            "summary": {
                "total": 10,
                "pending": 5,
                "completed": 3,
                "high_priority": 2
            },
            "voice_summary": "Hai 10 task, di cui 2 ad alta priorità. 5 sono in sospeso e 3 completati.",
            "ui_hints": {
                "display_mode": "list",
                "enable_swipe_actions": true,
                "enable_pull_to_refresh": true,
                "group_by": "category"
            }
        }

    Example usage (from chatbot):
        User: "Mostrami i miei task"
        Bot calls: get_tasks(authorization="Bearer eyJ...")
        Bot response:
          - Visual: Renders table/list with formatted data
          - Voice: Reads voice_summary
    """
    # Authenticate user
    user_id = verify_jwt_token(authorization)

    # Fetch tasks from FastAPI server
    tasks = await fastapi_client.get_tasks(user_id)

    # Format for React Native UI
    formatted_response = format_tasks_for_ui(tasks)

    return formatted_response


async def get_categories(authorization: str) -> Dict[str, Any]:
    """
    Get all categories for the authenticated user.

    Categories are used to organize tasks into groups like "Lavoro", "Personale", "Studio", etc.

    Authentication:
        Requires valid JWT token in Authorization header: "Bearer <token>"

    Returns:
        {
            "categories": [
                {
                    "category_id": 1,
                    "name": "Lavoro",
                    "description": "Task di lavoro",
                    "user_id": 123
                },
                ...
            ],
            "total": 5
        }

    Example usage:
        User: "Quali categorie ho?"
        Bot calls: get_categories(authorization="Bearer eyJ...")
        Bot response: "Hai 5 categorie: Lavoro, Personale, Studio, Sport, Famiglia"
    """
    # Authenticate user
    user_id = verify_jwt_token(authorization)

    # Fetch categories from FastAPI server
    categories = await fastapi_client.get_categories(user_id)

    return {
        "categories": categories,
        "total": len(categories)
    }


async def create_note(
    authorization: str,
    title: str,
    position_x: str = "0",
    position_y: str = "0",
    color: str = "#FFEB3B"
) -> Dict[str, Any]:
    """
    Create a new note (post-it style) for the authenticated user.

    Notes are simple text snippets that can be used for quick reminders, ideas, or lists.
    They have unlimited length and can be positioned on a canvas.

    Authentication:
        Requires valid JWT token in Authorization header: "Bearer <token>"

    Args:
        title: Note text content (unlimited length)
        position_x: X position on canvas (default: "0")
        position_y: Y position on canvas (default: "0")
        color: Note color in hex format (default: "#FFEB3B" yellow)
               Common colors:
               - "#FFEB3B" (yellow)
               - "#FF9800" (orange)
               - "#4CAF50" (green)
               - "#2196F3" (blue)
               - "#E91E63" (pink)
               - "#9C27B0" (purple)

    Returns:
        {
            "note_id": 456,
            "title": "Comprare il latte",
            "position_x": "0",
            "position_y": "0",
            "color": "#FFEB3B",
            "created_at": "2025-12-15T12:30:00",
            "message": "[OK] Nota creata con successo"
        }

    Example usage:
        User: "Crea una nota: Chiamare dentista domani"
        Bot calls: create_note(
            authorization="Bearer eyJ...",
            title="Chiamare dentista domani",
            color="#4CAF50"
        )
        Bot response: "[OK] Nota creata: 'Chiamare dentista domani'"
    """
    # Authenticate user
    user_id = verify_jwt_token(authorization)

    # Create note via FastAPI server
    note = await fastapi_client.create_note(
        user_id=user_id,
        title=title,
        position_x=position_x,
        position_y=position_y,
        color=color
    )

    return note


# ===== HEALTH CHECK =====

async def health_check() -> Dict[str, Any]:
    """
    Check health status of MCP server and FastAPI backend.

    This tool does NOT require authentication and can be used to verify
    that both the MCP server and the underlying FastAPI server are operational.

    Returns:
        {
            "mcp_server": "healthy",
            "fastapi_server": "healthy" | "unhealthy",
            "fastapi_url": "http://localhost:8080"
        }
    """
    fastapi_health = await fastapi_client.health_check()

    return {
        "mcp_server": "healthy",
        "fastapi_server": fastapi_health.get("status", "unknown"),
        "fastapi_url": settings.fastapi_base_url,
        "fastapi_details": fastapi_health
    }


# ===== REGISTER TOOLS =====

# Register the functions as MCP tools
mcp.tool()(get_tasks)
mcp.tool()(get_categories)
mcp.tool()(create_note)
mcp.tool()(health_check)


# ===== SERVER STARTUP =====

if __name__ == "__main__":

    print("=" * 60)
    print(f"[*] Starting {settings.mcp_server_name} v{settings.mcp_server_version}")
    print("=" * 60)
    print(f"FastAPI Backend: {settings.fastapi_base_url}")
    print(f"JWT Audience: {settings.mcp_audience}")
    print(f"Log Level: {settings.log_level}")
    print("=" * 60)
    print("\n[+] Available Tools:")
    print("  1. get_tasks - Get all user tasks (formatted for React Native)")
    print("  2. get_categories - Get user categories")
    print("  3. create_note - Create a new note")
    print("  4. health_check - Check server health (no auth required)")
    print("\n[+] Authentication: OAuth 2.1 JWT (Bearer token)")
    print("=" * 60)

    # Run the MCP server
    mcp.run()
