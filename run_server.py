#!/usr/bin/env python
"""
Convenience script to run the MCP HTTP server.

Usage:
    python run_server.py              # Run on default port 8000
    python run_server.py --port 8001  # Run on custom port
"""

import argparse
from src.http_server import run_server


def main():
    parser = argparse.ArgumentParser(description="Run MyTaskly MCP HTTP Server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )

    args = parser.parse_args()

    print(f"Starting MCP server on {args.host}:{args.port}...")
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
