"""
Simple configuration using environment variables.
"""

import os


def get_config():
    """Get configuration from environment variables with sensible defaults"""
    return {
        # Server settings
        'host': os.getenv('ANKICONNECT_HOST', '127.0.0.1'),
        'port': int(os.getenv('ANKICONNECT_PORT', '8765')),
        'debug': os.getenv('ANKICONNECT_DEBUG', 'false').lower() in ('true', '1', 'yes'),

        # API settings
        'api_key': os.getenv('ANKICONNECT_API_KEY'),
        'api_version': int(os.getenv('ANKICONNECT_API_VERSION', '6')),

        # CORS settings
        'cors_origins': os.getenv('ANKICONNECT_CORS_ORIGINS', 'http://localhost').split(','),

        # Anki settings
        'collection_path': os.getenv('ANKICONNECT_COLLECTION_PATH'),
    }


def get_ankiconnect_config():
    """Get configuration in AnkiConnect plugin format"""
    config = get_config()
    return {
        'apiKey': config['api_key'],
        'apiLogPath': None,
        'apiPollInterval': 25,
        'apiVersion': config['api_version'],
        'webBacklog': 5,
        'webBindAddress': config['host'],
        'webBindPort': config['port'],
        'webCorsOrigin': None,
        'webCorsOriginList': config['cors_origins'],
        'ignoreOriginList': [],
        'webTimeout': 10000,
    }
