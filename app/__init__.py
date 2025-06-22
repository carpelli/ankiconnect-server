import os
import sys
import types
from typing import Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import GUI stubs before importing anything that uses aqt
from .gui_stubs import install_gui_stubs
install_gui_stubs()

import aqt

# Mock the necessary Anki environment for the plugin
class MockAnkiMainWindow:
    def __init__(self, collection_path: str):
        # Import anki after setting up the path
        from anki.collection import Collection

        self.col = Collection(collection_path)
        self.addonManager = MockAddonManager()

    def close(self):
        if hasattr(self, 'col') and self.col:
            self.col.close()

class MockAddonManager:
    def getConfig(self, name):
        # Return default AnkiConnect configuration
        return {
            'apiKey': None,
            'apiLogPath': None,
            'apiPollInterval': 25,
            'apiVersion': 6,
            'webBacklog': 5,
            'webBindAddress': '127.0.0.1',
            'webBindPort': 8765,
            'webCorsOrigin': None,
            'webCorsOriginList': ['http://localhost'],
            'ignoreOriginList': [],
            'webTimeout': 10000,
        }

class AnkiConnectBridge:
    """
    Minimal bridge that wraps the existing AnkiConnect plugin
    """

    def __init__(self, collection_path: Optional[str] = None):
        # Set up the mock Anki environment
        self.collection_path = collection_path or self._find_collection_path()
        self.mock_mw = MockAnkiMainWindow(self.collection_path)

        # Patch aqt.mw to point to our mock
        aqt.mw = self.mock_mw

        # Import and initialize AnkiConnect
        try:
            from ..libs.ankiconnect.plugin import AnkiConnect
        except ImportError:
            # Handle case when run directly - add libs directory to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            libs_dir = os.path.join(current_dir, '..', 'libs')
            libs_dir = os.path.abspath(libs_dir)
            if libs_dir not in sys.path:
                sys.path.insert(0, libs_dir)
            from ankiconnect.plugin import AnkiConnect

        self.ankiconnect = AnkiConnect()

        # Don't start the web server since we'll handle HTTP ourselves
        # Just initialize logging if needed
        try:
            self.ankiconnect.initLogging()
        except:
            pass

    def _find_collection_path(self) -> str:
        """Find the default Anki collection path"""
        if sys.platform == "win32":
            base_path = os.path.expanduser("~/AppData/Roaming/Anki2")
        elif sys.platform == "darwin":
            base_path = os.path.expanduser("~/Library/Application Support/Anki2")
        else:
            base_path = os.path.expanduser("~/.local/share/Anki2")

        # Look for User 1 profile (default)
        user1_path = os.path.join(base_path, "User 1", "collection.anki2")
        if os.path.exists(user1_path):
            return user1_path

        # Fallback - return the expected path anyway
        return user1_path

    def process_request(self, request_data: dict) -> dict:
        """Process an AnkiConnect request using the original plugin"""
        try:
            # Use the original AnkiConnect handler
            return self.ankiconnect.handler(request_data)
        except Exception as e:
            # Return error in AnkiConnect format
            return {"result": None, "error": str(e)}

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'mock_mw'):
            self.mock_mw.close()

# Flask application
app = Flask(__name__)
CORS(app)

# Global bridge instance
bridge = None

def get_bridge():
    """Get or create the bridge instance"""
    global bridge
    if bridge is None:
        bridge = AnkiConnectBridge()
    return bridge

@app.route("/", methods=["POST"])
def handle_request():
    """Handle AnkiConnect API requests"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"result": None, "error": "No JSON data received"})

        # Process the request using the original AnkiConnect plugin
        result = get_bridge().process_request(data)
        return jsonify(result)

    except Exception as e:
        return jsonify({"result": None, "error": str(e)})

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "version": "1.0.0"})

def run_server(host: str = "127.0.0.1", port: int = 8765, debug: bool = False):
    """Run the AnkiConnect bridge server"""
    print(f"Starting AnkiConnect Bridge on {host}:{port}")
    bridge_instance = get_bridge()
    print(f"Collection path: {bridge_instance.collection_path}")

    try:
        app.run(host=host, port=port, debug=debug)
    finally:
        # Clean up on shutdown
        if bridge_instance:
            bridge_instance.close()

if __name__ == "__main__":
    run_server(debug=True)
