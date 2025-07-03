"""
Simple configuration using environment variables.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables with sensible defaults"""
    return {
        'host': os.getenv('ANKICONNECT_HOST', '127.0.0.1'),
        'port': int(os.getenv('ANKICONNECT_PORT', '8765')),
        'debug': os.getenv('ANKICONNECT_DEBUG', 'false').lower() in ('true', '1', 'yes'),

        'api_key': os.getenv('ANKICONNECT_API_KEY'),
        'api_log_path': os.getenv('ANKICONNECT_API_LOG_PATH'),

        'sync_endpoint': os.getenv('SYNC_ENDPOINT'),
        'sync_key': os.getenv('SYNC_KEY'),

        'cors_origins': os.getenv('ANKICONNECT_CORS_ORIGINS', 'http://localhost').split(','),

        'collection_path': os.getenv('ANKICONNECT_COLLECTION_PATH'),
    }


def get_ankiconnect_config() -> Dict[str, Any]:
    """Get configuration in AnkiConnect plugin format"""
    config = get_config()
    return {
        'apiKey': config['api_key'],
        'apiLogPath': config['api_log_path'],
        'apiPollInterval': 25,
        'apiVersion': 6,
        'webBacklog': 5,
        'webBindAddress': config['host'],
        'webBindPort': config['port'],
        'webCorsOrigin': None,
        'webCorsOriginList': config['cors_origins'],
        'ignoreOriginList': [],
        'webTimeout': 10000,
    }
