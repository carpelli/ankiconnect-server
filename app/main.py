import logging
from typing import Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

from app.core import AnkiConnectBridge
from app.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get config
config = get_config()

# Flask application
app = Flask(__name__)
CORS(app, origins=config['cors_origins'])

# Global bridge instance (will be set in run_server)
bridge = None

@app.route("/", methods=["POST"])
def handle_request():
    """Handle AnkiConnect API requests"""
    global bridge
    try:
        if bridge is None:
            logger.error("Bridge not initialized")
            return jsonify({"result": None, "error": "Server not properly initialized"}), 500
            
        data = request.get_json(force=True)
        if not data:
            logger.warning("No JSON data received in request")
            return jsonify({"result": None, "error": "No JSON data received"}), 400

        # Check API key if configured
        if config['api_key']:
            provided_key = data.get('key')
            if provided_key != config['api_key']:
                logger.warning(f"Invalid API key provided: {provided_key}")
                return jsonify({"result": None, "error": "Invalid API key"}), 403

        # Process the request using the original AnkiConnect plugin
        logger.debug(f"Processing request: {data.get('action', 'unknown')}")
        result = bridge.process_request(data)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({"result": None, "error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    global bridge
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "collection_path": bridge.collection_path if bridge else None,
        "api_key_set": bool(config['api_key'])
    })

def run_server(host: Optional[str] = None, port: Optional[int] = None, debug: Optional[bool] = None):
    """Run the AnkiConnect bridge server"""
    global bridge

    # Use config defaults if not specified
    host = host or config['host']
    port = port or config['port']
    debug = debug if debug is not None else config['debug']

    logger.info(f"Starting AnkiConnect Bridge on {host}:{port}")

    # Use context manager for automatic cleanup
    with AnkiConnectBridge() as bridge:
        logger.info(f"Collection path: {bridge.collection_path}")

        if config['api_key']:
            logger.info("🔐 API key authentication enabled")
        else:
            logger.warning("⚠️ No API key set (consider setting ANKICONNECT_API_KEY)")

        logger.info("Running in single-threaded mode (like original AnkiConnect)")

        try:
            # Run Flask in single-threaded mode to match AnkiConnect's behavior
            # This prevents concurrent access to the Anki database
            app.run(host=host, port=port, threaded=False, debug=debug, use_reloader=False)
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)

if __name__ == "__main__":
    run_server()
