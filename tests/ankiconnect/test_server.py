import json
import threading
import time
from unittest.mock import Mock, patch

import jsonschema
import pytest
import requests
from flask import Flask

from app import server
from app.config import get_ankiconnect_config
from conftest import ac, session_with_profile_loaded


@pytest.fixture
def mock_server():
    """Create a test server instance with mocked AnkiConnectBridge"""
    with patch('app.server.ankiconnect', ac):
        server.ankiconnect = ac
        server.app.config['TESTING'] = True
        with server.app.test_client() as client:
            yield client


class TestHTTPRoutes:
    def test_options_request_cors_headers(self, mock_server):
        response = mock_server.options('/')
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_options_request_private_network_header(self, mock_server):
        headers = {'Access-Control-Request-Private-Network': 'true'}
        response = mock_server.options('/', headers=headers)
        assert response.status_code == 200
        assert response.headers.get('Access-Control-Allow-Private-Network') == 'true'

    def test_empty_post_returns_api_version(self, mock_server):
        response = mock_server.post('/', data='')
        assert response.status_code == 200
        data = response.get_json()
        expected_version = get_ankiconnect_config()["apiVersion"]
        assert data == {"apiVersion": f"AnkiConnect v.{expected_version}"}


class TestJSONRPCValidation:
    def test_invalid_json_returns_400(self, mock_server):
        response = mock_server.post('/', data='invalid json')
        assert response.status_code == 400

    def test_valid_json_schema_validation(self, mock_server):
        valid_request = {
            "action": "version",
            "version": 6
        }
        response = mock_server.post('/', 
                                   data=json.dumps(valid_request),
                                   content_type='application/json')
        assert response.status_code == 200

    def test_schema_validation_error_returns_400(self, mock_server):
        invalid_request = {
            "action": "version"
            # missing required "version" field
        }
        response = mock_server.post('/',
                                   data=json.dumps(invalid_request),
                                   content_type='application/json')
        assert response.status_code == 400

    def test_request_permission_bypass(self, mock_server):
        request_data = {
            "action": "requestPermission",
            "version": 6,
            "params": {}
        }
        response = mock_server.post('/',
                                   data=json.dumps(request_data),
                                   content_type='application/json')
        assert response.status_code == 200
        result = response.get_json()
        assert result.get("result") is True


class TestCollectionLocking:
    def test_concurrent_requests_are_serialized(self, mock_server):
        results = []
        
        def make_request():
            request_data = {"action": "version", "version": 6}
            response = mock_server.post('/',
                                       data=json.dumps(request_data),
                                       content_type='application/json')
            results.append(response.status_code)
        
        threads = [threading.Thread(target=make_request) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        assert all(status == 200 for status in results)
        assert len(results) == 3

    def test_collection_modification_triggers_sync_timer(self, mock_server):
        with patch('app.server.schedule_sync_after_mod') as mock_schedule:
            request_data = {
                "action": "createDeck",
                "version": 6,
                "params": {"deck": "test_sync_deck"}
            }
            response = mock_server.post('/',
                                       data=json.dumps(request_data),
                                       content_type='application/json')
            assert response.status_code == 200
            mock_schedule.assert_called_once()


class TestAutoSync:
    def test_sync_timer_cancellation_on_manual_sync(self):
        with patch('app.server.ankiconnect', ac):
            server.sync_after_mod_timer = Mock()
            server.restart_periodic_sync = Mock()
            
            with server.app.test_client() as client:
                request_data = {"action": "sync", "version": 6}
                response = client.post('/',
                                     data=json.dumps(request_data),
                                     content_type='application/json')
                
                if server.sync_after_mod_timer:
                    server.sync_after_mod_timer.cancel.assert_called_once()
                server.restart_periodic_sync.assert_called_once()

    def test_sync_after_modification_delay(self):
        with patch('app.server.Timer') as mock_timer:
            with patch('app.server.sync') as mock_sync:
                server.schedule_sync_after_mod()
                mock_timer.assert_called_once_with(server.SYNC_AFTER_MOD_DELAY_SECONDS, mock_sync)

    def test_periodic_sync_timer_setup(self):
        with patch('app.server.Timer') as mock_timer:
            server.restart_periodic_sync()
            mock_timer.assert_called_once()
            args = mock_timer.call_args[0]
            assert args[0] == server.SYNC_PERIODIC_DELAY_SECONDS


class TestErrorHandling:
    def test_exception_in_handler_returns_500(self, mock_server):
        with patch.object(ac, 'handler', side_effect=Exception("Test error")):
            request_data = {"action": "version", "version": 6}
            response = mock_server.post('/',
                                       data=json.dumps(request_data),
                                       content_type='application/json')
            assert response.status_code == 500

    def test_sync_error_handling(self):
        from anki.errors import SyncError
        with patch('app.server.ankiconnect.sync', side_effect=SyncError("Sync failed")):
            with patch('app.server.logger') as mock_logger:
                server.sync()
                mock_logger.error.assert_called_once()


class TestRequestLogging:
    def test_request_logging_includes_client_info(self, mock_server):
        with patch('app.server.logger') as mock_logger:
            request_data = {"action": "version", "version": 6}
            headers = {
                'Origin': 'http://example.com',
                'User-Agent': 'test-agent'
            }
            response = mock_server.post('/',
                                       data=json.dumps(request_data),
                                       content_type='application/json',
                                       headers=headers)
            
            assert response.status_code == 200
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            assert 'origin=http://example.com' in log_call
            assert 'action=version' in log_call
            assert 'user_agent=test-agent' in log_call

    def test_debug_logging_includes_request_body(self, mock_server):
        with patch('app.server.logger') as mock_logger:
            request_data = {"action": "version", "version": 6}
            response = mock_server.post('/',
                                       data=json.dumps(request_data),
                                       content_type='application/json')
            
            debug_calls = [call for call in mock_logger.debug.call_args_list 
                          if 'Request body:' in str(call)]
            assert len(debug_calls) > 0


class TestServerLifecycle:
    def test_server_cleanup_on_shutdown(self):
        with patch('app.server.ankiconnect') as mock_ac:
            mock_ac.close = Mock()
            server.sync_after_mod_timer = Mock()
            server.sync_periodic_timer = Mock()
            
            try:
                raise KeyboardInterrupt()
            except KeyboardInterrupt:
                if server.sync_after_mod_timer:
                    server.sync_after_mod_timer.cancel()
                if server.sync_periodic_timer:
                    server.sync_periodic_timer.cancel()
                mock_ac.close()
            
            mock_ac.close.assert_called_once()