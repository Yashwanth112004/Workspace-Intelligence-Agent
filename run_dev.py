#!/usr/bin/env python
"""
Workspace Intelligence Agent (WIA) - Daemon Runner
Starts the local WIA backend server daemon for CLI and VS Code extension.
"""
import subprocess
import sys
import os
import argparse

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

def run_backend(port: int = 8000, reload: bool = True):
    """Run the FastAPI backend using Uvicorn"""
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)]
    if reload:
        cmd.append("--reload")
    print("==========================================================")
    print(" 🚀 Workspace Intelligence Agent (WIA) Engine Daemon")
    print("==========================================================")
    print(f" Engine API:   http://127.0.0.1:{port}")
    print(f" API Docs:     http://127.0.0.1:{port}/docs")
    print(" Ready for WIA CLI and VS Code Extension connections.")
    print("==========================================================")
    print("\nPress Ctrl+C to stop daemon\n")
    subprocess.run(cmd, cwd=BACKEND_DIR)

def main():
    parser = argparse.ArgumentParser(description="WIA Local Engine Daemon Runner")
    parser.add_argument("--port", type=int, default=8000, help="Backend API port (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    args = parser.parse_args()

    try:
        run_backend(port=args.port, reload=not args.no_reload)
    except KeyboardInterrupt:
        print("\nShutting down WIA engine daemon...")
        sys.exit(0)

if __name__ == "__main__":
    main()