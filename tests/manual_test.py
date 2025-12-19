"""Manual test script for MCP server."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth import create_test_token
from src.server import get_tasks, get_categories, create_note, health_check
from src.config import settings


async def main():
    """Run manual tests of MCP server."""
    print("=" * 70)
    print("MyTaskly MCP Server - Manual Test")
    print("=" * 70)
    print(f"FastAPI Backend: {settings.fastapi_base_url}")
    print(f"JWT Audience: {settings.mcp_audience}")
    print("=" * 70)

    # Test 1: Health Check (no auth)
    print("\n1. Testing health_check (no authentication required)...")
    try:
        health = await health_check()
        print(f"   OK MCP Server: {health['mcp_server']}")
        print(f"   OK FastAPI Server: {health['fastapi_server']}")
        print(f"   FastAPI URL: {health['fastapi_url']}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # Generate test token
    print("\n2. Generating test JWT token for user_id=1...")
    try:
        token = create_test_token(user_id=1, expires_minutes=30)
        print(f"   OK Token generated: {token[:60]}...")
        auth_header = f"Bearer {token}"
    except Exception as e:
        print(f"   ERROR: {e}")
        return

    # Test 2: Get Tasks
    print("\n3. Testing get_tasks (with authentication)...")
    try:
        tasks_response = await get_tasks(authorization=auth_header)
        print(f"   OK Response type: {tasks_response['type']}")
        print(f"   OK Total tasks: {tasks_response['summary']['total']}")
        print(f"   OK Pending: {tasks_response['summary']['pending']}")
        print(f"   OK High priority: {tasks_response['summary']['high_priority']}")
        print(f"\n   Voice Summary:")
        print(f"      {tasks_response['voice_summary']}")

        if tasks_response['tasks']:
            print(f"\n   First task example:")
            first_task = tasks_response['tasks'][0]
            print(f"      - ID: {first_task['id']}")
            print(f"      - Title: {first_task['title']}")
            print(f"      - Category: {first_task['category']} ({first_task['categoryColor']})")
            print(f"      - Priority: {first_task['priority']} {first_task['priorityEmoji']}")
            print(f"      - Date: {first_task['endTimeFormatted']}")

    except Exception as e:
        print(f"   ERROR: {e}")

    # Test 3: Get Categories
    print("\n4. Testing get_categories (with authentication)...")
    try:
        categories_response = await get_categories(authorization=auth_header)
        print(f"   OK Total categories: {categories_response['total']}")

        if categories_response['categories']:
            print(f"\n   Categories:")
            for cat in categories_response['categories'][:5]:  # Show first 5
                print(f"      - {cat['name']}: {cat.get('description', 'No description')}")

    except Exception as e:
        print(f"   ERROR: {e}")

    # Test 4: Create Note
    print("\n5. Testing create_note (with authentication)...")
    try:
        note_response = await create_note(
            authorization=auth_header,
            title="Test note from MCP server - " + str(asyncio.get_event_loop().time()),
            color="#4CAF50"
        )
        print(f"   OK Note created!")
        print(f"      - ID: {note_response['note_id']}")
        print(f"      - Title: {note_response['title']}")
        print(f"      - Color: {note_response['color']}")
        print(f"      - Message: {note_response['message']}")

    except Exception as e:
        print(f"   ERROR: {e}")

    # Test 5: Invalid Token
    print("\n6. Testing with invalid token (should fail)...")
    try:
        await get_tasks(authorization="Bearer invalid_token_12345")
        print(f"   ERROR Should have failed!")
    except Exception as e:
        print(f"   OK Correctly rejected: {str(e)[:80]}...")

    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
