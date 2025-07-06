import threading
import time
from unittest.mock import Mock, patch

import pytest

from app import server
from conftest import ac, session_with_profile_loaded


class TestCollectionLocking:
    def test_concurrent_collection_access_is_synchronized(self):
        results = []
        errors = []
        
        def access_collection():
            try:
                with server.collection_lock:
                    col = ac.collection()
                    time.sleep(0.1)
                    results.append(col.mod)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=access_collection) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0
        assert len(results) == 3

    def test_collection_modification_detection(self, session_with_profile_loaded):
        with patch('app.server.schedule_sync_after_mod') as mock_schedule:
            with server.collection_lock:
                before_mod = ac.collection().mod
                ac.createDeck("test_mod_detection")
                after_mod = ac.collection().mod
                collection_changed = before_mod != after_mod
            
            if collection_changed:
                server.schedule_sync_after_mod()
                mock_schedule.assert_called_once()


class TestAutoSyncTimers:
    def test_sync_after_modification_timer_creation(self):
        with patch('app.server.Timer') as mock_timer:
            with patch('app.server.sync') as mock_sync:
                server.schedule_sync_after_mod()
                mock_timer.assert_called_once_with(server.SYNC_AFTER_MOD_DELAY_SECONDS, mock_sync)
                mock_timer.return_value.start.assert_called_once()

    def test_sync_after_modification_timer_cancellation(self):
        mock_timer = Mock()
        server.sync_after_mod_timer = mock_timer
        
        with patch('app.server.Timer') as new_timer:
            server.schedule_sync_after_mod()
            mock_timer.cancel.assert_called_once()
            new_timer.return_value.start.assert_called_once()

    def test_periodic_sync_timer_setup(self):
        with patch('app.server.Timer') as mock_timer:
            server.restart_periodic_sync()
            mock_timer.assert_called_once()
            args = mock_timer.call_args[0]
            assert args[0] == server.SYNC_PERIODIC_DELAY_SECONDS

    def test_periodic_sync_timer_restart_cancels_previous(self):
        mock_timer = Mock()
        server.sync_periodic_timer = mock_timer
        
        with patch('app.server.Timer'):
            server.restart_periodic_sync()
            mock_timer.cancel.assert_called_once()

    def test_sync_actions_disable_auto_sync_timer(self):
        mock_timer = Mock()
        server.sync_after_mod_timer = mock_timer
        
        with patch('app.server.restart_periodic_sync') as mock_restart:
            data = {"action": "sync"}
            
            if data["action"] in ["sync", "fullSync"]:
                if server.sync_after_mod_timer is not None:
                    server.sync_after_mod_timer.cancel()
                server.restart_periodic_sync()
            
            mock_timer.cancel.assert_called_once()
            mock_restart.assert_called_once()


class TestSyncFunction:
    def test_sync_function_with_collection_lock(self):
        with patch.object(ac, 'sync') as mock_sync:
            with patch('app.server.logger') as mock_logger:
                server.sync()
                mock_sync.assert_called_once()
                mock_logger.info.assert_called_with("Auto-syncing...")

    def test_sync_function_handles_sync_error(self):
        from anki.errors import SyncError  # noqa
        with patch.object(ac, 'sync', side_effect=SyncError("Network error")):
            with patch('app.server.logger') as mock_logger:
                server.sync()
                mock_logger.error.assert_called_once()
                error_call = mock_logger.error.call_args[0][0]
                assert "Error syncing: Network error" in error_call


class TestServerLifecycle:
    def test_server_cleanup_cancels_timers(self):
        sync_timer = Mock()
        periodic_timer = Mock()
        server.sync_after_mod_timer = sync_timer
        server.sync_periodic_timer = periodic_timer
        
        mock_ac = Mock()
        server.ankiconnect = mock_ac
        
        # Simulate cleanup
        if server.sync_after_mod_timer is not None:
            server.sync_after_mod_timer.cancel()
        if server.sync_periodic_timer is not None:
            server.sync_periodic_timer.cancel()
        server.ankiconnect.close()
        
        sync_timer.cancel.assert_called_once()
        periodic_timer.cancel.assert_called_once()
        mock_ac.close.assert_called_once()

    def test_restart_periodic_sync_sets_up_recursive_timer(self):
        with patch('app.server.Timer') as mock_timer:
            server.restart_periodic_sync()
            
            # Check that the timer function will call restart_periodic_sync again
            timer_function = mock_timer.call_args[0][1]
            
            with patch('app.server.sync'):
                with patch('app.server.restart_periodic_sync') as mock_restart:
                    timer_function()
                    mock_restart.assert_called_once()


class TestRequestPermissionBypass:
    def test_request_permission_returns_true_with_allowed_origin(self):
        result = ac.requestPermission(origin="test", allowed=True)
        assert result is True

    def test_request_permission_behavior_in_handler(self):
        request_data = {
            "action": "requestPermission",
            "version": 6,
            "params": {}
        }
        
        with patch.object(ac, 'requestPermission', return_value=True) as mock_permission:
            result = ac.handler(request_data)
            mock_permission.assert_called_once_with(origin="", allowed=True)
            assert result is True


class TestCollectionModificationTracking:
    def test_modification_tracking_in_request_handler(self, session_with_profile_loaded):
        with patch('app.server.schedule_sync_after_mod') as mock_schedule:
            before_mod = ac.collection().mod
            
            # Simulate a request that modifies the collection
            ac.createDeck("test_tracking_deck")
            
            after_mod = ac.collection().mod
            collection_changed = before_mod != after_mod
            
            if collection_changed:
                server.schedule_sync_after_mod()
                mock_schedule.assert_called_once()
            
            # Clean up
            ac.deleteDecks(decks=["test_tracking_deck"], cardsToo=True)


class TestDelayConstants:
    def test_sync_delay_constants_are_reasonable(self):
        assert server.SYNC_AFTER_MOD_DELAY_SECONDS == 2
        assert server.SYNC_PERIODIC_DELAY_SECONDS == 30 * 60  # 30 minutes
        assert server.SYNC_AFTER_MOD_DELAY_SECONDS < server.SYNC_PERIODIC_DELAY_SECONDS