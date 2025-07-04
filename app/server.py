import logging
from threading import Timer, Lock

from flask import Flask, request, jsonify
from flask_cors import CORS
from waitress import serve
from anki.errors import SyncError

from app.core import AnkiConnectBridge
from app.config import get_config

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


@app.route("/", methods=["POST"])
def handle_request():
    """Handle AnkiConnect API requests"""
    global ankiconnect
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            logger.warning("Incorrect or empty JSON data received in request")
            return jsonify({"result": None, "error": "incorrect or empty JSON data received in request"}), 400

        client_ip = request.remote_addr or "unknown"
        action = data.get("action")
        origin = request.headers.get("Origin", "unknown")
        user_agent = request.headers.get("User-Agent", "unknown")
        logger.info(
            f"Request from {client_ip} | origin={origin} | action={action} | user_agent={user_agent}"
        )

        with collection_lock:
            before = ankiconnect.collection().mod
            result = ankiconnect.handler(data)
            if (
                data["action"] not in ["sync", "fullSync"]
                and before != ankiconnect.collection().mod
            ):
                logger.debug(f"Collection modified")
                schedule_sync_after_mod()
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        # Return error in AnkiConnect format (same as original)
        error_response = {"result": None, "error": str(e)}
        return jsonify(error_response), 500


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


def periodic_sync(skip=False):
    global sync_periodic_timer
    if not skip:
        sync()
    sync_periodic_timer = Timer(SYNC_PERIODIC_DELAY, periodic_sync)
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
        periodic_sync(skip=True)
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
