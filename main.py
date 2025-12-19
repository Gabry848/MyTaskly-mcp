#!/usr/bin/env python
"""
Run the MyTaskly MCP server with all registered tools.

Usage:
    python run_server.py              # Run MCP server in stdio mode
"""

from src.core.server import mcp
from src.config import settings



if __name__ == "__main__":
    # Run the MCP server
    print("[+] Starting MCP server in stdio mode...")
    print("[+] Ready to accept connections\n")
    mcp.run()
