import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("ANKICONNECT_HOST", "127.0.0.1")
PORT = int(os.getenv("ANKICONNECT_PORT", "8765"))
DEBUG = os.getenv("ANKICONNECT_DEBUG", "false").lower() in ("true", "1", "yes")

API_KEY = os.getenv("ANKICONNECT_API_KEY")

SYNC_ENDPOINT = os.getenv("SYNC_ENDPOINT")
SYNC_KEY = os.getenv("SYNC_KEY")

CORS_ORIGINS = os.getenv("ANKICONNECT_CORS_ORIGINS", "http://localhost").split(",")

_base_dir_str = os.getenv("ANKI_BASE_DIR")
ANKI_BASE_DIR = Path(_base_dir_str) if _base_dir_str is not None else None


def get_ankiconnect_config():
    """Get configuration in AnkiConnect plugin format"""
    return {
        "apiKey": API_KEY,
        "apiLogPath": None,
        "apiPollInterval": 25,
        "apiVersion": 6,
        "webBacklog": 5,
        "webBindAddress": HOST,
        "webBindPort": PORT,
        "webCorsOrigin": None,
        "webCorsOriginList": CORS_ORIGINS,
        "ignoreOriginList": [],
        "webTimeout": 10000,
    }
