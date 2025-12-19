"""Tests for data formatters."""

import pytest
from src.formatters import (
    format_date_for_mobile,
    get_priority_emoji,
    get_priority_color,
    get_category_color,
    format_tasks_for_ui
)


def test_format_date_for_mobile():
    """Test date formatting for mobile display."""
    # Test with valid ISO date
    date_str = "2025-12-15T18:00:00+00:00"
    result = format_date_for_mobile(date_str)
    assert "dicembre" in result.lower()
    assert "18:00" in result

    # Test with empty string
    assert format_date_for_mobile("") == ""


def test_get_priority_emoji():
    """Test priority emoji mapping."""
    assert get_priority_emoji("Alta") == "⚡"
    assert get_priority_emoji("Media") == ""
    assert get_priority_emoji("Bassa") == ""


def test_get_priority_color():
    """Test priority color mapping."""
    assert get_priority_color("Alta") == "#EF4444"
    assert get_priority_color("Media") == "#F59E0B"
    assert get_priority_color("Bassa") == "#10B981"


def test_get_category_color():
    """Test category color mapping."""
    # Test predefined categories
    assert get_category_color("Lavoro") == "#3B82F6"
    assert get_category_color("Personale") == "#8B5CF6"

    # Test custom category (should hash to consistent color)
    color1 = get_category_color("CustomCategory")
    color2 = get_category_color("CustomCategory")
    assert color1 == color2  # Consistent hashing
    assert color1.startswith("#")


def test_format_tasks_for_ui():
    """Test complete task formatting for UI."""
    tasks = [
        {
            "task_id": 1,
            "title": "Test Task",
            "description": "Test description",
            "end_time": "2025-12-15T18:00:00+00:00",
            "start_time": None,
            "priority": "Alta",
            "status": "In sospeso",
            "category": "Lavoro"
        }
    ]

    result = format_tasks_for_ui(tasks)

    # Check structure
    assert result["type"] == "task_list"
    assert "tasks" in result
    assert "summary" in result
    assert "voice_summary" in result
    assert "columns" in result

    # Check task formatting
    task = result["tasks"][0]
    assert task["id"] == 1
    assert task["title"] == "Test Task"
    assert task["priorityEmoji"] == "⚡"
    assert task["categoryColor"] == "#3B82F6"

    # Check summary
    assert result["summary"]["total"] == 1
    assert result["summary"]["high_priority"] == 1

    # Check voice summary
    assert "1 task" in result["voice_summary"].lower()
