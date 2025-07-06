import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest  # noqa

from app.core import AnkiConnectBridge
from conftest import ac, session_with_profile_loaded


class TestBridgeInitialization:
    def test_bridge_creates_collection_path_correctly(self):
        temp_dir = Path(tempfile.mkdtemp())
        bridge = AnkiConnectBridge(base_dir=temp_dir)
        
        expected_path = str(temp_dir.absolute() / "collection.anki2")
        assert bridge.collection_path == expected_path
        
        bridge.close()

    def test_bridge_sets_up_mock_main_window(self):
        temp_dir = Path(tempfile.mkdtemp())
        bridge = AnkiConnectBridge(base_dir=temp_dir)
        
        assert hasattr(bridge, 'mock_mw')
        assert bridge.mock_mw is not None
        
        bridge.close()

    def test_bridge_patches_aqt_mw(self):
        import aqt  # noqa
        temp_dir = Path(tempfile.mkdtemp())
        
        original_mw = aqt.mw
        bridge = AnkiConnectBridge(base_dir=temp_dir)
        
        assert aqt.mw == bridge.mock_mw
        
        bridge.close()


class TestBridgeRequestHandling:
    def test_request_permission_action_bypass(self, session_with_profile_loaded):
        request_data = {
            "action": "requestPermission",
            "version": 6,
            "params": {}
        }
        
        result = ac.handler(request_data)
        assert result is True

    def test_normal_actions_go_through_parent_handler(self, session_with_profile_loaded):
        with patch('app.plugin.AnkiConnect.handler') as mock_parent:
            mock_parent.return_value = {"result": "test", "error": None}
            
            request_data = {
                "action": "version",
                "version": 6,
                "params": {}
            }
            
            result = ac.handler(request_data)
            mock_parent.assert_called_once_with(request_data)
            assert result == {"result": "test", "error": None}


class TestBridgeSyncAuthentication:
    def test_sync_auth_requires_sync_key(self):
        with patch('app.core.SYNC_KEY', None):
            with pytest.raises(Exception, match="sync: key not configured"):
                ac.sync_auth()

    def test_sync_auth_creates_auth_object_with_key(self):
        with patch('app.core.SYNC_KEY', 'test_hkey'):
            with patch('app.core.SYNC_ENDPOINT', 'https://test.example.com'):
                auth = ac.sync_auth()
                
                assert auth.hkey == 'test_hkey'
                assert auth.endpoint == 'https://test.example.com'
                assert auth.io_timeout_secs == 10

    def test_sync_auth_default_timeout_configuration(self):
        with patch('app.core.SYNC_KEY', 'test_key'):
            auth = ac.sync_auth()
            assert auth.io_timeout_secs == 10


class TestBridgeCleanup:
    def test_close_cleans_up_mock_main_window(self):
        temp_dir = Path(tempfile.mkdtemp())
        bridge = AnkiConnectBridge(base_dir=temp_dir)
        
        with patch.object(bridge.mock_mw, 'close') as mock_close:
            bridge.close()
            mock_close.assert_called_once()

    def test_close_handles_missing_mock_mw_gracefully(self):
        temp_dir = Path(tempfile.mkdtemp())
        bridge = AnkiConnectBridge(base_dir=temp_dir)
        
        delattr(bridge, 'mock_mw')
        
        # Should not raise an exception
        bridge.close()

    def test_close_handles_exceptions_during_cleanup(self):
        temp_dir = Path(tempfile.mkdtemp())
        bridge = AnkiConnectBridge(base_dir=temp_dir)
        
        with patch.object(bridge.mock_mw, 'close', side_effect=Exception("Cleanup error")):
            with patch('app.core.logger') as mock_logger:
                bridge.close()
                mock_logger.error.assert_called_once()


class TestBridgeIntegration:
    def test_bridge_collection_access_works(self, session_with_profile_loaded):
        col = ac.collection()
        assert col is not None
        assert hasattr(col, 'mod')

    def test_bridge_inherits_ankiconnect_functionality(self, session_with_profile_loaded):
        # Test that basic AnkiConnect methods work
        version = ac.version()
        assert version == 6
        
        # Test deck operations
        deck_id = ac.createDeck("test_integration_deck")
        assert isinstance(deck_id, int)
        
        deck_names = ac.deckNames()
        assert "test_integration_deck" in deck_names
        
        # Clean up
        ac.deleteDecks(decks=["test_integration_deck"], cardsToo=True)

    def test_bridge_log_attribute_initialization(self):
        temp_dir = Path(tempfile.mkdtemp())
        bridge = AnkiConnectBridge(base_dir=temp_dir)
        
        assert bridge.log is None
        
        bridge.close()


class TestBridgePathHandling:
    def test_bridge_handles_relative_paths(self):
        relative_path = Path("test_collection")
        bridge = AnkiConnectBridge(base_dir=relative_path)
        
        expected_path = str(relative_path.absolute() / "collection.anki2")
        assert bridge.collection_path == expected_path
        
        bridge.close()

    def test_bridge_handles_absolute_paths(self):
        absolute_path = Path(tempfile.mkdtemp()).absolute()
        bridge = AnkiConnectBridge(base_dir=absolute_path)
        
        expected_path = str(absolute_path / "collection.anki2")
        assert bridge.collection_path == expected_path
        
        bridge.close()


class TestBridgeLogging:
    def test_bridge_logs_initialization(self):
        with patch('app.core.logger') as mock_logger:
            temp_dir = Path(tempfile.mkdtemp())
            bridge = AnkiConnectBridge(base_dir=temp_dir)
            
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("Initializing with collection:" in call for call in log_calls)
            assert any("AnkiConnect bridge initialized successfully" in call for call in log_calls)
            
            bridge.close()

    def test_bridge_logs_cleanup_success(self):
        with patch('app.core.logger') as mock_logger:
            temp_dir = Path(tempfile.mkdtemp())
            bridge = AnkiConnectBridge(base_dir=temp_dir)
            bridge.close()
            
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("Bridge resources cleaned up" in call for call in log_calls)

    def test_bridge_logs_cleanup_errors(self):
        with patch('app.core.logger') as mock_logger:
            temp_dir = Path(tempfile.mkdtemp())
            bridge = AnkiConnectBridge(base_dir=temp_dir)
            
            with patch.object(bridge.mock_mw, 'close', side_effect=Exception("Test error")):
                bridge.close()
                
                error_calls = [str(call) for call in mock_logger.error.call_args_list]
                assert any("Error during cleanup: Test error" in call for call in error_calls)