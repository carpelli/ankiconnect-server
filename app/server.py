import logging
from threading import Lock, Timer

import jsonschema
from anki.errors import SyncError
from flask import Flask, jsonify, request
from flask_cors import CORS
from waitress import serve

from app.config import get_ankiconnect_config, get_config
from app.core import AnkiConnectBridge
from app.plugin import web

SYNC_AFTER_MOD_DELAY = 2
SYNC_PERIODIC_DELAY = 1 * 60

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get config
config = get_config()

# Flask application
app = Flask(__name__)
CORS(app, origins=config["cors_origins"])

ankiconnect: AnkiConnectBridge

collection_lock = Lock()
sync_after_mod_timer = None
sync_periodic_timer = None

# The API version reported by the original plugin configuration
API_VERSION = get_ankiconnect_config()["apiVersion"]


# -----------------------------------------------------------------------------
# HTTP routes to mirror /libs/ankiconnect/plugin/web.py
# -----------------------------------------------------------------------------


# Pre-flight CORS / OPTIONS handler
@app.route("/", methods=["OPTIONS"])
def handle_options():
    """Return minimal CORS pre-flight response (includes private-network header)."""
    resp = app.make_default_options_response()
    if request.headers.get("Access-Control-Request-Private-Network", "false") == "true":
        resp.headers["Access-Control-Allow-Private-Network"] = "true"
    return resp


# Main JSON-RPC handler
@app.route("/", methods=["POST"])
def handle_request():
    """Handle AnkiConnect API requests (JSON RPC style)"""
    global ankiconnect

    # Parse and validate JSON body
    try:
        data = request.get_json(force=True)
        jsonschema.validate(data, web.request_schema)
    except (ValueError, jsonschema.ValidationError) as e:
        if len(request.get_data()) == 0:
            return {"version": API_VERSION}, 200
        else:
            logger.info("JSON parse/validation failed")
            return {"result": None, "error": str(e)}, 400

    # Log
    client_ip = request.remote_addr or "unknown"
    action = data.get("action")
    origin = request.headers.get("Origin", "unknown")
    user_agent = request.headers.get("User-Agent", "unknown")
    logger.info(
        f"Request from {client_ip} | origin={origin} | action={action} | user_agent={user_agent}"
    )

    # Handle request through AnkiConnectBridge
    try:
        with collection_lock:
            before_mod = ankiconnect.collection().mod
            result = ankiconnect.handler(data)
            collection_changed = before_mod != ankiconnect.collection().mod
        if action in ["sync", "fullSync"]:
            # disable/restart sync timers if we already synced
            if sync_after_mod_timer is not None:
                sync_after_mod_timer.cancel()
            restart_periodic_sync()
        elif collection_changed:
            logger.debug("Collection modified – scheduling auto-sync")
            schedule_sync_after_mod()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return {"result": None, "error": str(e)}, 500


def sync():
    with collection_lock:
        logger.info("Auto-syncing...")
        try:
            ankiconnect.sync()
        except SyncError as e:
            logger.error(f"Error syncing: {e}")


def schedule_sync_after_mod():
    global sync_after_mod_timer
    if sync_after_mod_timer is not None:
        sync_after_mod_timer.cancel()
    sync_timer = Timer(SYNC_AFTER_MOD_DELAY, sync)
    sync_timer.start()


def restart_periodic_sync():
    global sync_periodic_timer
    if sync_periodic_timer is not None:
        sync_periodic_timer.cancel()

    def _periodic():
        sync()
        restart_periodic_sync()

    sync_periodic_timer = Timer(SYNC_PERIODIC_DELAY, _periodic)
    sync_periodic_timer.start()


def run_server(
    host: str | None = None, port: int | None = None, debug: bool | None = None
):
    """Run the AnkiConnect bridge server"""
    global ankiconnect

    # Use config defaults if not specified
    host = host or config["host"]
    port = port or config["port"]
    debug = debug if debug is not None else config["debug"]

    if config["api_key"]:
        logger.info("🔐 API key authentication enabled")
    else:
        logger.warning("⚠️ No API key set (consider setting ANKICONNECT_API_KEY)")

    # Initialize the bridge
    ankiconnect = AnkiConnectBridge()
    logger.info(f"Sync endpoint: {ankiconnect.sync_auth().endpoint or 'AnkiWeb'}")

    try:
        restart_periodic_sync()
        serve(app, host=host, port=port, threads=1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        # Clean up the bridge
        if sync_after_mod_timer is not None:
            sync_after_mod_timer.cancel()
        if sync_periodic_timer is not None:
            sync_periodic_timer.cancel()
        ankiconnect.close()


if __name__ == "__main__":
    run_server()
