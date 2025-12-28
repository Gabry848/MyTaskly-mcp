#!/usr/bin/env python
"""
Test client to connect to MyTaskly MCP server via SSE.

Usage:
    python test_mcp_client.py
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_server():
    """Test connection to MyTaskly MCP server."""

    # MCP server URL
    server_url = "https://mcp.mytasklyapp.com/sse"

    logger.info(f"Connecting to MCP server at {server_url}...")

    try:
        # Connect to the SSE server
        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                init_result = await session.initialize()

                logger.info("✅ Successfully connected to MCP server!")
                logger.info(f"Server info: {init_result.serverInfo}")

                # List available tools
                tools = await session.list_tools()
                logger.info(f"\n📦 Available tools ({len(tools.tools)}):")
                for tool in tools.tools:
                    logger.info(f"  - {tool.name}: {tool.description}")

                # Example: Call health_check tool
                logger.info("\n🔍 Testing health_check tool...")
                result = await session.call_tool("health_check", {})
                logger.info(f"Health check result: {result}")

                logger.info("\n✨ Test completed successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to connect to MCP server: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
