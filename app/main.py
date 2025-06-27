from typing import Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import our simple config and Anki mocks
from app.core import AnkiConnectBridge
from app.config import get_config

# Get config
config = get_config()

# Flask application
app = Flask(__name__)
CORS(app, origins=config['cors_origins'])

@app.route("/", methods=["POST"])
def handle_request():
    """Handle AnkiConnect API requests"""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"result": None, "error": "No JSON data received"})

        # Check API key if configured
        if config['api_key']:
            provided_key = data.get('key')
            if provided_key != config['api_key']:
                return jsonify({"result": None, "error": "Invalid API key"}), 403

        # Process the request using the original AnkiConnect plugin
        result = bridge.process_request(data)
        return jsonify(result)

    except Exception as e:
        return jsonify({"result": None, "error": str(e)})

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "collection_path": bridge.collection_path,
        "api_key_set": bool(config['api_key'])
    })

def run_server(host: Optional[str] = None, port: Optional[int] = None, debug: Optional[bool] = None):
    """Run the AnkiConnect bridge server"""

    # Use config defaults if not specified
    host = host or config['host']
    port = port or config['port']
    debug = debug if debug is not None else config['debug']

    print(f"Starting AnkiConnect Bridge on {host}:{port}")

    print(f"Collection path: {bridge.collection_path}")

    if config['api_key']:
        print("🔐 API key authentication enabled")
    else:
        print("⚠️ No API key set (consider setting ANKICONNECT_API_KEY)")

    print("Running in single-threaded mode (like original AnkiConnect)")

    try:
        # Run Flask in single-threaded mode to match AnkiConnect's behavior
        # This prevents concurrent access to the Anki database
        app.run(host=host, port=port, threaded=False)
    finally:
        # Clean up on shutdown
        bridge.close()

if __name__ == "__main__":
    bridge = AnkiConnectBridge()
    run_server()
