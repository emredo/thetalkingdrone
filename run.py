#!/usr/bin/env python
"""Run script for the Talking Drone application."""

import argparse
import os
import sys
from pathlib import Path

import uvicorn

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for running the application."""
    parser = argparse.ArgumentParser(description="Run the Talking Drone API server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload (enabled by default)",
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Disable debug mode (enabled by default)",
    )
    parser.add_argument(
        "--log-level",
        default="debug",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: debug)",
    )

    args = parser.parse_args()

    # Set defaults for development
    debug_mode = not args.no_debug
    reload_mode = not args.no_reload

    # Set environment variables
    if debug_mode:
        os.environ["DEBUG"] = "true"

    # Set PYTHONPATH to include project root
    os.environ["PYTHONPATH"] = str(project_root)

    print("🚁 Starting Talking Drone API Server...")
    print(f"📍 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔄 Reload: {reload_mode}")
    print(f"🐛 Debug: {debug_mode}")
    print(f"📊 Log Level: {args.log_level}")
    print(f"📁 Project Root: {project_root}")
    print(f"🔗 Access your app at: http://localhost:{args.port}")
    print(f"📚 API Documentation: http://localhost:{args.port}/docs")
    print("-" * 50)

    try:
        uvicorn.run(
            "src:create_app",
            host=args.host,
            port=args.port,
            reload=reload_mode,
            factory=True,
            log_level=args.log_level,
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
