import os
from unittest.mock import patch

import pytest  # noqa

from app.config import get_ankiconnect_config, HOST, PORT, API_KEY, CORS_ORIGINS, SYNC_ENDPOINT, SYNC_KEY, ANKI_BASE_DIR, LOGLEVEL


class TestEnvironmentConfiguration:
    def test_default_host_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            from app.config import HOST
            # Re-import to get fresh values
            import importlib
            import app.config
            importlib.reload(app.config)
            assert app.config.HOST == "127.0.0.1"

    def test_host_from_environment(self):
        with patch.dict(os.environ, {"ANKICONNECT_HOST": "0.0.0.0"}):
            import importlib
            import app.config
            importlib.reload(app.config)
            assert app.config.HOST == "0.0.0.0"

    def test_default_port_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import app.config
            importlib.reload(app.config)
            assert app.config.PORT == 8765

    def test_port_from_environment(self):
        with patch.dict(os.environ, {"ANKICONNECT_PORT": "9999"}):
            import importlib
            import app.config
            importlib.reload(app.config)
            assert app.config.PORT == 9999

    def test_api_key_from_environment(self):
        with patch.dict(os.environ, {"ANKICONNECT_API_KEY": "test-key-123"}):
            import importlib
            import app.config
            importlib.reload(app.config)
            assert app.config.API_KEY == "test-key-123"

    def test_cors_origins_parsing(self):
        with patch.dict(os.environ, {"ANKICONNECT_CORS_ORIGINS": "http://localhost,https://example.com"}):
            import importlib
            import app.config
            importlib.reload(app.config)
            assert app.config.CORS_ORIGINS == ["http://localhost", "https://example.com"]

    def test_sync_configuration(self):
        with patch.dict(os.environ, {
            "SYNC_ENDPOINT": "https://sync.example.com",
            "SYNC_KEY": "sync-key-123"
        }):
            import importlib
            import app.config
            importlib.reload(app.config)
            assert app.config.SYNC_ENDPOINT == "https://sync.example.com"
            assert app.config.SYNC_KEY == "sync-key-123"

    def test_loglevel_configuration(self):
        with patch.dict(os.environ, {"ANKICONNECT_LOGLEVEL": "DEBUG"}):
            import importlib
            import app.config
            importlib.reload(app.config)
            assert app.config.LOGLEVEL == "DEBUG"


class TestAnkiConnectConfigGeneration:
    def test_config_structure(self):
        config = get_ankiconnect_config()
        
        required_keys = [
            "apiKey", "apiLogPath", "apiPollInterval", "apiVersion",
            "webBacklog", "webBindAddress", "webBindPort", "webCorsOrigin",
            "webCorsOriginList", "ignoreOriginList", "webTimeout"
        ]
        
        for key in required_keys:
            assert key in config

    def test_config_values_match_environment(self):
        with patch.dict(os.environ, {
            "ANKICONNECT_API_KEY": "test-api-key",
            "ANKICONNECT_HOST": "192.168.1.100",
            "ANKICONNECT_PORT": "8888",
            "ANKICONNECT_CORS_ORIGINS": "http://app1.com,http://app2.com"
        }):
            import importlib
            import app.config
            importlib.reload(app.config)
            
            config = app.config.get_ankiconnect_config()
            
            assert config["apiKey"] == "test-api-key"
            assert config["webBindAddress"] == "192.168.1.100"
            assert config["webBindPort"] == 8888
            assert config["webCorsOriginList"] == ["http://app1.com", "http://app2.com"]

    def test_config_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import app.config
            importlib.reload(app.config)
            
            config = app.config.get_ankiconnect_config()
            
            assert config["apiKey"] is None
            assert config["apiLogPath"] is None
            assert config["apiPollInterval"] == 25
            assert config["apiVersion"] == 6
            assert config["webBacklog"] == 5
            assert config["webBindAddress"] == "127.0.0.1"
            assert config["webBindPort"] == 8765
            assert config["webCorsOrigin"] is None
            assert config["webCorsOriginList"] == ["http://localhost"]
            assert config["ignoreOriginList"] == []
            assert config["webTimeout"] == 10000


class TestConfigurationValidation:
    def test_port_type_conversion(self):
        with patch.dict(os.environ, {"ANKICONNECT_PORT": "invalid"}):
            with pytest.raises(ValueError):
                import importlib
                import app.config
                importlib.reload(app.config)

    def test_missing_required_config_handled_gracefully(self):
        # Test that missing optional config doesn't break anything
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import app.config
            importlib.reload(app.config)
            
            # Should not raise exceptions
            assert app.config.API_KEY is None
            assert app.config.SYNC_ENDPOINT is None
            assert app.config.SYNC_KEY is None
            assert app.config.ANKI_BASE_DIR is None