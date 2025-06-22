#!/usr/bin/env python3
"""
AnkiConnect Bridge Runner
Installs dependencies and starts the server
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Check if requirements.txt exists
    if os.path.exists("requirements.txt"):
        install_dependencies()

    # Import and run the server
    try:
        from app import run_server
        print("\n" + "="*50)
        print("AnkiConnect Bridge Server")
        print("="*50)
        print("This server translates AnkiConnect API requests")
        print("to Python anki module operations.")
        print("\nEndpoint: http://127.0.0.1:8765")
        print("Health check: http://127.0.0.1:8765/health")
        print("\nPress Ctrl+C to stop the server")
        print("="*50 + "\n")

        run_server(debug=True)

    except ImportError as e:
        print(f"Failed to import app module: {e}")
        print("Make sure all dependencies are installed")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
