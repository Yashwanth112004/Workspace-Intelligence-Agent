#!/usr/bin/env python
"""
Workspace Intelligence Agent (WIA) - Development Launcher
Runs backend FastAPI, React Vite dashboard, or Streamlit client.
"""
import subprocess
import sys
import os
import time
import threading
import argparse

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

def run_backend(port: int = 8000, reload: bool = True):
    """Run the FastAPI backend using Uvicorn"""
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)]
    if reload:
        cmd.append("--reload")
    subprocess.run(cmd, cwd=BACKEND_DIR)

def run_frontend(port: int = 5173):
    """Run the React + Vite frontend"""
    subprocess.run(["npm", "run", "dev", "--", "--port", str(port)], cwd=FRONTEND_DIR, shell=True)

def run_streamlit(port: int = 8501):
    """Run the Streamlit frontend client"""
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port)], cwd=FRONTEND_DIR)

def main():
    parser = argparse.ArgumentParser(description="WIA Development Environment Launcher")
    parser.add_argument("--backend-only", action="store_true", help="Start only FastAPI backend")
    parser.add_argument("--frontend-only", action="store_true", help="Start only React frontend")
    parser.add_argument("--streamlit", action="store_true", help="Start Streamlit interface instead of React")
    parser.add_argument("--port", type=int, default=8000, help="Backend API port (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=5173, help="Frontend React port (default: 5173)")
    args = parser.parse_args()

    print("==========================================================")
    print(" 🚀 Workspace Intelligence Agent (WIA) Dev Environment")
    print("==========================================================")

    if args.backend_only:
        print(f" Backend API:  http://localhost:{args.port}")
        print(f" API Docs:     http://localhost:{args.port}/docs")
        print("==========================================================")
        run_backend(port=args.port)
        return

    if args.frontend_only:
        print(f" React UI:     http://localhost:{args.frontend_port}")
        print("==========================================================")
        run_frontend(port=args.frontend_port)
        return

    if args.streamlit:
        print(f" Backend API:  http://localhost:{args.port}")
        print(f" Streamlit UI: http://localhost:8501")
        print("==========================================================")
        t = threading.Thread(target=lambda: run_backend(port=args.port), daemon=True)
        t.start()
        time.sleep(2)
        run_streamlit()
        return

    # Default: Full-stack (FastAPI + React Vite)
    print(f" Backend API:  http://localhost:{args.port}")
    print(f" API Docs:     http://localhost:{args.port}/docs")
    print(f" React UI:     http://localhost:{args.frontend_port}")
    print("==========================================================")
    print("\nPress Ctrl+C to stop both services\n")

    backend_thread = threading.Thread(target=lambda: run_backend(port=args.port), daemon=True)
    backend_thread.start()

    time.sleep(2)

    try:
        run_frontend(port=args.frontend_port)
    except KeyboardInterrupt:
        print("\nShutting down WIA dev servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()