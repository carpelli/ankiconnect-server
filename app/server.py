import argparse
import json
import logging
from pathlib import Path
from threading import Lock, Timer

import jsonschema
from flask import Flask, jsonify, request
from flask_cors import CORS
from waitress import serve

from app import plugin
from app.config import (
    ANKI_BASE_DIR,
    API_KEY,
    CORS_ORIGINS,
    HOST,
    LOGLEVEL,
    PORT,
    get_ankiconnect_config,
)
from app.core import AnkiConnectBridge

SYNC_AFTER_MOD_DELAY_SECONDS = 2
SYNC_PERIODIC_DELAY_SECONDS = 30 * 60

# Configure logging
logging.basicConfig(
    level=LOGLEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Flask application
app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)

ankiconnect: AnkiConnectBridge

collection_lock = Lock()
sync_after_mod_timer = None
sync_periodic_timer = None

# The API version reported by the original plugin configuration
API_VERSION = get_ankiconnect_config()["apiVersion"]


# -----------------------------------------------------------------------------
# HTTP routes to mirror libs/ankiconnect/plugin/web.py
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
        data = json.loads(request.get_data().decode("utf-8"))
        jsonschema.validate(data, plugin.web.request_schema)
    except (ValueError, jsonschema.ValidationError) as e:
        if len(request.get_data()) == 0:
            return {"apiVersion": f"AnkiConnect v.{API_VERSION}"}, 200
        else:
            logger.info("JSON parse/validation failed")
            return plugin.web.format_exception_reply(API_VERSION, e), 400

    # Log
    client_ip = request.remote_addr or "unknown"
    action = data.get("action")
    origin = request.headers.get("Origin", "unknown")
    user_agent = request.headers.get("User-Agent", "unknown")
    logger.info(
        f"Request from {client_ip} | origin={origin} | action={action} | user_agent={user_agent}"
    )
    logger.debug(f"Request body: {data}")

    # Handle request through AnkiConnectBridge
    try:
        with collection_lock:
            result = ankiconnect.handler(data)
            collection_changed = ankiconnect.check_and_update_modified()
        logger.debug(f"Reply body: {result}")
        if action in ["sync", "fullSync"]:
            # disable/restart sync timers if we already synced
            if sync_after_mod_timer is not None:
                sync_after_mod_timer.cancel()
            restart_periodic_sync()
        elif collection_changed:
            logger.debug("Collection modified – scheduling auto-sync")
            schedule_sync_after_mod()

        # For API version <= 4: result is the raw value (string, number, list, etc.)
        # For API version > 4: result is already an object with result/error fields
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return plugin.web.format_exception_reply(data.get("version", 6), e), 500


def sync():
    with collection_lock:
        logger.info("Auto-syncing...")
        try:
            ankiconnect.sync()
        except Exception as e:
            logger.error(f"Error syncing: {e}")


def schedule_sync_after_mod():
    global sync_after_mod_timer
    if sync_after_mod_timer is not None:
        sync_after_mod_timer.cancel()
    sync_after_mod_timer = Timer(SYNC_AFTER_MOD_DELAY_SECONDS, sync)
    sync_after_mod_timer.start()


def restart_periodic_sync():
    global sync_periodic_timer
    if sync_periodic_timer is not None:
        sync_periodic_timer.cancel()

    def _periodic():
        sync()
        restart_periodic_sync()

    sync_periodic_timer = Timer(SYNC_PERIODIC_DELAY_SECONDS, _periodic)
    sync_periodic_timer.start()


def run_server(base_dir: Path):
    global ankiconnect

    ankiconnect = AnkiConnectBridge(base_dir)
    logger.info(f"Sync endpoint: {ankiconnect.sync_auth().endpoint or 'AnkiWeb'}")

    try:
        restart_periodic_sync()
        serve(app, host=HOST, port=PORT, threads=1)
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


parser = argparse.ArgumentParser(description="AnkiConnect server")
parser.add_argument("--base", "-b", type=Path, help="base directory for the collection")
parser.add_argument(
    "--create", action="store_true", help="create a new collection if not present"
)


if __name__ == "__main__":
    args = parser.parse_args()
    if not (base_dir := args.base or ANKI_BASE_DIR):
        logger.error("Collection directory not set, use -b or ANKI_BASE_DIR")
        exit(1)
    base_dir = Path(base_dir)
    if not base_dir.is_dir():
        logger.error(f"Collection directory not a directory: {base_dir.resolve()}")
        exit(1)
    collection_path = base_dir / "collection.anki2"
    if not collection_path.exists() and not args.create:
        logger.error(
            f"Collection not found at {collection_path}, use --create to create a new collection"
        )
        exit(1)
    if API_KEY:
        logger.info("API key authentication enabled")
    else:
        logger.warning("No API key set (consider setting ANKICONNECT_API_KEY)")
    run_server(base_dir)
