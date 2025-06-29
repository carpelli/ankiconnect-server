import logging

from flask import Flask, request, jsonify
from flask_cors import CORS
from waitress import serve

from app.core import AnkiConnectBridge
from app.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get config
config = get_config()

# Flask application
app = Flask(__name__)
CORS(app, origins=config['cors_origins'])

# Global bridge instance
bridge: AnkiConnectBridge

@app.route("/", methods=["POST"])
def handle_request():
    """Handle AnkiConnect API requests"""
    global bridge
    try:
        data = request.get_json(force=True)
        if not data:
            logger.warning("No JSON data received in request")
            return jsonify({"result": None, "error": "No JSON data received"}), 400

        # Process the request using the original AnkiConnect plugin
        logger.debug(f"Processing request: {data.get('action', 'unknown')}")
        result = bridge.handle_request(data)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        # Return error in AnkiConnect format (same as original)
        error_response = {"result": None, "error": str(e)}
        return jsonify(error_response), 500

def run_server(host: str | None = None, port: int | None = None, debug: bool | None = None):
    """Run the AnkiConnect bridge server"""
    global bridge

    # Use config defaults if not specified
    host = host or config['host']
    port = port or config['port']
    debug = debug if debug is not None else config['debug']

    if config['api_key']:
        logger.info("🔐 API key authentication enabled")
    else:
        logger.warning("⚠️ No API key set (consider setting ANKICONNECT_API_KEY)")

    logger.info(f"Starting AnkiConnect Bridge on {host}:{port}")

    # Initialize the bridge
    bridge = AnkiConnectBridge()
    bridge.login(config['sync_username'], config['sync_password'], config['sync_endpoint'])

    try:
        serve(app, host=host, port=port, threads=1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        # Clean up the bridge
        bridge.close()

if __name__ == "__main__":
    run_server()
