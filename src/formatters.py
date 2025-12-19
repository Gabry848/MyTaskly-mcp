"""Data formatters for transforming FastAPI responses to MCP-friendly formats."""

from typing import Dict, Any, List
from datetime import datetime


def format_date_for_mobile(date_str: str) -> str:
    """
    Format ISO date string to mobile-friendly format.

    Args:
        date_str: ISO format date string (e.g., "2025-12-15T18:00:00+00:00")

    Returns:
        Formatted string (e.g., "Venerdì 15 dicembre, 18:00")
    """
    if not date_str:
        return ""

    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        # Italian day names
        days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        months = [
            "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
            "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
        ]

        day_name = days[dt.weekday()]
        month_name = months[dt.month - 1]

        return f"{day_name} {dt.day} {month_name}, {dt.strftime('%H:%M')}"
    except Exception:
        return date_str


def get_priority_emoji(priority: str) -> str:
    """Get emoji for task priority."""
    priority_map = {
        "Alta": "[!]",
        "Media": "",
        "Bassa": ""
    }
    return priority_map.get(priority, "")


def get_priority_color(priority: str) -> str:
    """Get color for task priority."""
    color_map = {
        "Alta": "#EF4444",  # Red
        "Media": "#F59E0B",  # Orange
        "Bassa": "#10B981"   # Green
    }
    return color_map.get(priority, "#6B7280")


def get_category_color(category_name: str) -> str:
    """
    Get a consistent color for a category based on its name.
    Uses a simple hash to generate consistent colors.
    """
    if not category_name:
        return "#6B7280"

    # Predefined colors for common categories
    predefined = {
        "Lavoro": "#3B82F6",      # Blue
        "Personale": "#8B5CF6",   # Purple
        "Studio": "#10B981",      # Green
        "Sport": "#F59E0B",       # Orange
        "Famiglia": "#EC4899",    # Pink
        "Cibo": "#EF4444",        # Red
        "Generale": "#6B7280"     # Gray
    }

    if category_name in predefined:
        return predefined[category_name]

    # Generate color from hash
    hash_val = sum(ord(c) for c in category_name)
    colors = ["#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", "#EC4899", "#EF4444"]
    return colors[hash_val % len(colors)]


def format_tasks_for_ui(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format tasks response for React Native UI components.

    This creates a JSON structure optimized for native mobile components
    with all necessary data for rendering without additional processing.

    Args:
        tasks: List of task dictionaries from FastAPI

    Returns:
        Formatted dictionary with type, tasks, columns, and metadata
    """
    formatted_tasks = []

    for task in tasks:
        # Extract and format data
        priority = task.get("priority", "Media")
        category_name = task.get("category", {}).get("name", "Generale") if isinstance(task.get("category"), dict) else task.get("category", "Generale")

        formatted_task = {
            "id": task.get("task_id"),
            "title": task.get("title", ""),
            "description": task.get("description", ""),
            "endTime": task.get("end_time"),
            "endTimeFormatted": format_date_for_mobile(task.get("end_time")) if task.get("end_time") else None,
            "startTime": task.get("start_time"),
            "category": category_name,
            "categoryColor": get_category_color(category_name),
            "priority": priority,
            "priorityEmoji": get_priority_emoji(priority),
            "priorityColor": get_priority_color(priority),
            "status": task.get("status", "In sospeso"),
            "actions": {
                "complete": {
                    "label": "[OK] Completa",
                    "enabled": task.get("status") != "Completato"
                },
                "edit": {
                    "label": "✏️ Modifica",
                    "enabled": True
                },
                "delete": {
                    "label": "🗑️ Elimina",
                    "enabled": True
                }
            }
        }
        formatted_tasks.append(formatted_task)

    # Calculate summary statistics
    total = len(formatted_tasks)
    pending = sum(1 for t in formatted_tasks if t["status"] == "In sospeso")
    completed = sum(1 for t in formatted_tasks if t["status"] == "Completato")
    high_priority = sum(1 for t in formatted_tasks if t["priority"] == "Alta")

    # Create voice summary for TTS
    voice_summary = f"Hai {total} task"
    if high_priority > 0:
        voice_summary += f", di cui {high_priority} ad alta priorità"
    if pending > 0:
        voice_summary += f". {pending} sono in sospeso"
    if completed > 0:
        voice_summary += f" e {completed} completati"
    voice_summary += "."

    return {
        "type": "task_list",
        "version": "1.0",
        "columns": [
            {
                "id": "title",
                "label": "Task",
                "width": "40%",
                "sortable": True
            },
            {
                "id": "endTimeFormatted",
                "label": "Scadenza",
                "width": "30%",
                "sortable": True
            },
            {
                "id": "category",
                "label": "Categoria",
                "width": "20%",
                "filterable": True
            },
            {
                "id": "priority",
                "label": "Priorità",
                "width": "10%",
                "filterable": True
            }
        ],
        "tasks": formatted_tasks,
        "summary": {
            "total": total,
            "pending": pending,
            "completed": completed,
            "high_priority": high_priority
        },
        "voice_summary": voice_summary,
        "ui_hints": {
            "display_mode": "list",  # or "table", "grid"
            "enable_swipe_actions": True,
            "enable_pull_to_refresh": True,
            "group_by": "category"  # optional grouping
        }
    }
