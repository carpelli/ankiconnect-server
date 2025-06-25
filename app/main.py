import os
import sys
from typing import Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import GUI stubs before importing anything that uses aqt
from .gui_stubs import install_gui_stubs
install_gui_stubs()

# Import our simple config and Anki mocks
from .config import get_config
from .anki_mocks import MockAnkiMainWindow, find_collection_path

import aqt

class AnkiConnectBridge:
    """
    Minimal bridge that wraps the existing AnkiConnect plugin
    """

    def __init__(self, collection_path: Optional[str] = None):
        # Set up the mock Anki environment
        self.collection_path = collection_path or find_collection_path()
        self.mock_mw = MockAnkiMainWindow(self.collection_path)

        # Patch aqt.mw to point to our mock
        aqt.mw = self.mock_mw

        # Add libs directory to path to fix import issues
        current_dir = os.path.dirname(os.path.abspath(__file__))
        libs_dir = os.path.join(current_dir, '..', 'libs')
        libs_dir = os.path.abspath(libs_dir)
        if libs_dir not in sys.path:
            sys.path.insert(0, libs_dir)

        # Import and initialize AnkiConnect
        from ankiconnect.plugin import AnkiConnect
        self.ankiconnect = AnkiConnect()

        # Initialize logging if needed
        try:
            self.ankiconnect.initLogging()
        except:
            pass

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

# Get config
config = get_config()

# Flask application
app = Flask(__name__)
CORS(app, origins=config['cors_origins'])

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

        # Check API key if configured
        if config['api_key']:
            provided_key = data.get('key')
            if provided_key != config['api_key']:
                return jsonify({"result": None, "error": "Invalid API key"}), 403

        # Process the request using the original AnkiConnect plugin
        result = get_bridge().process_request(data)
        return jsonify(result)

    except Exception as e:
        return jsonify({"result": None, "error": str(e)})

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    bridge_instance = get_bridge()
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "collection_path": bridge_instance.collection_path,
        "api_key_set": bool(config['api_key'])
    })

def run_server(host: Optional[str] = None, port: Optional[int] = None, debug: Optional[bool] = None):
    """Run the AnkiConnect bridge server"""

    # Use config defaults if not specified
    host = host or config['host']
    port = port or config['port']
    debug = debug if debug is not None else config['debug']

    print(f"Starting AnkiConnect Bridge on {host}:{port}")

    bridge_instance = get_bridge()
    print(f"Collection path: {bridge_instance.collection_path}")

    if config['api_key']:
        print("🔐 API key authentication enabled")
    else:
        print("⚠️ No API key set (consider setting ANKICONNECT_API_KEY)")

    print("Running in single-threaded mode (like original AnkiConnect)")

    try:
        # Run Flask in single-threaded mode to match AnkiConnect's behavior
        # This prevents concurrent access to the Anki database
        app.run(host=host, port=port, debug=debug, threaded=False)
    finally:
        # Clean up on shutdown
        if bridge_instance:
            bridge_instance.close()

if __name__ == "__main__":
    run_server(debug=True)
