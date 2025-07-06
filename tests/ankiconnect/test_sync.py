import pytest
from unittest.mock import Mock, patch

import anki.sync
from anki.errors import SyncError

from conftest import ac, session_with_profile_loaded, current_decks_and_models_etc_preserved


class TestSyncAuthentication:
    def test_sync_auth_creation_with_valid_config(self):
        with patch('app.core.SYNC_KEY', 'test_key'):
            with patch('app.core.SYNC_ENDPOINT', 'https://test.ankiweb.net'):
                auth = ac.sync_auth()
                assert auth.hkey == 'test_key'
                assert auth.endpoint == 'https://test.ankiweb.net'
                assert auth.io_timeout_secs == 10

    def test_sync_auth_missing_key_raises_exception(self):
        with patch('app.core.SYNC_KEY', None):
            with pytest.raises(Exception, match="sync: key not configured"):
                ac.sync_auth()

    def test_sync_auth_default_endpoint(self):
        with patch('app.core.SYNC_KEY', 'test_key'):
            with patch('app.core.SYNC_ENDPOINT', None):
                auth = ac.sync_auth()
                assert auth.hkey == 'test_key'
                assert auth.endpoint is None


class TestBasicSync:
    def test_sync_successful_no_changes(self, session_with_profile_loaded):
        with current_decks_and_models_etc_preserved():
            with patch.object(ac, 'sync_auth') as mock_auth:
                mock_auth.return_value = Mock(hkey='test', endpoint=None, io_timeout_secs=10)
                
                with patch.object(ac.collection(), 'sync_collection') as mock_sync:
                    mock_output = Mock()
                    mock_output.NO_CHANGES = 0
                    mock_output.NORMAL_SYNC = 1
                    mock_output.required = mock_output.NO_CHANGES
                    mock_sync.return_value = mock_output
                    
                    result = ac.sync()
                    assert result is None
                    mock_sync.assert_called_once()

    def test_sync_successful_normal_sync(self, session_with_profile_loaded):
        with current_decks_and_models_etc_preserved():
            with patch.object(ac, 'sync_auth') as mock_auth:
                mock_auth.return_value = Mock(hkey='test', endpoint=None, io_timeout_secs=10)
                
                with patch.object(ac.collection(), 'sync_collection') as mock_sync:
                    mock_output = Mock()
                    mock_output.NO_CHANGES = 0
                    mock_output.NORMAL_SYNC = 1
                    mock_output.required = mock_output.NORMAL_SYNC
                    mock_sync.return_value = mock_output
                    
                    result = ac.sync()
                    assert result is None
                    mock_sync.assert_called_once_with(mock_auth.return_value, True)

    def test_sync_requires_full_sync_raises_exception(self, session_with_profile_loaded):
        with current_decks_and_models_etc_preserved():
            with patch.object(ac, 'sync_auth') as mock_auth:
                mock_auth.return_value = Mock(hkey='test', endpoint=None, io_timeout_secs=10)
                
                with patch.object(ac.collection(), 'sync_collection') as mock_sync:
                    mock_output = Mock()
                    mock_output.NO_CHANGES = 0
                    mock_output.NORMAL_SYNC = 1
                    mock_output.FULL_SYNC_REQUIRED = 2
                    mock_output.required = mock_output.FULL_SYNC_REQUIRED
                    
                    with patch.object(anki.sync.SyncOutput.ChangesRequired, 'Name') as mock_name:
                        mock_name.return_value = "FULL_SYNC_REQUIRED"
                        mock_sync.return_value = mock_output
                        
                        with pytest.raises(Exception, match="could not sync status FULL_SYNC_REQUIRED - use fullSync"):
                            ac.sync()


class TestFullSync:
    def test_full_sync_upload(self, session_with_profile_loaded):
        with current_decks_and_models_etc_preserved():
            with patch.object(ac, 'sync_auth') as mock_auth:
                mock_auth.return_value = Mock(hkey='test', endpoint=None, io_timeout_secs=10)
                
                with patch.object(ac.collection(), 'sync_collection') as mock_sync:
                    with patch.object(ac.collection(), 'close_for_full_sync') as mock_close:
                        with patch.object(ac.collection(), 'full_upload_or_download') as mock_full:
                            with patch.object(ac.collection(), 'reopen') as mock_reopen:
                                mock_output = Mock()
                                mock_output.NO_CHANGES = 0
                                mock_output.NORMAL_SYNC = 1
                                mock_output.FULL_SYNC_REQUIRED = 2
                                mock_output.required = mock_output.FULL_SYNC_REQUIRED
                                mock_output.server_media_usn = 123
                                mock_sync.return_value = mock_output
                                
                                result = ac.fullSync(mode="upload")
                                assert result is None
                                
                                mock_close.assert_called_once()
                                mock_full.assert_called_once_with(
                                    auth=mock_auth.return_value,
                                    server_usn=123,
                                    upload=True
                                )
                                mock_reopen.assert_called_once()

    def test_full_sync_download(self, session_with_profile_loaded):
        with current_decks_and_models_etc_preserved():
            with patch.object(ac, 'sync_auth') as mock_auth:
                mock_auth.return_value = Mock(hkey='test', endpoint=None, io_timeout_secs=10)
                
                with patch.object(ac.collection(), 'sync_collection') as mock_sync:
                    with patch.object(ac.collection(), 'close_for_full_sync') as mock_close:
                        with patch.object(ac.collection(), 'full_upload_or_download') as mock_full:
                            with patch.object(ac.collection(), 'reopen') as mock_reopen:
                                mock_output = Mock()
                                mock_output.NO_CHANGES = 0
                                mock_output.NORMAL_SYNC = 1
                                mock_output.FULL_SYNC_REQUIRED = 2
                                mock_output.required = mock_output.FULL_SYNC_REQUIRED
                                mock_output.server_media_usn = 456
                                mock_sync.return_value = mock_output
                                
                                result = ac.fullSync(mode="download")
                                assert result is None
                                
                                mock_close.assert_called_once()
                                mock_full.assert_called_once_with(
                                    auth=mock_auth.return_value,
                                    server_usn=456,
                                    upload=False
                                )
                                mock_reopen.assert_called_once()


class TestDatabaseIntegrity:
    def test_check_database_no_problems(self, session_with_profile_loaded):
        with patch.object(ac.collection(), 'fix_integrity') as mock_fix:
            mock_fix.return_value = ("", True)
            
            result = ac.checkDatabase()
            assert result == {"problems": "", "ok": True}
            mock_fix.assert_called_once()

    def test_check_database_with_problems(self, session_with_profile_loaded):
        with patch.object(ac.collection(), 'fix_integrity') as mock_fix:
            problems_text = "Problem 1\nProblem 2\n"
            mock_fix.return_value = (problems_text, False)
            
            result = ac.checkDatabase()
            assert result == {"problems": problems_text, "ok": False}
            mock_fix.assert_called_once()

    def test_check_database_logging(self, session_with_profile_loaded):
        with patch('app.core.logger') as mock_logger:
            with patch.object(ac.collection(), 'fix_integrity') as mock_fix:
                mock_fix.return_value = ("Database repaired\n", True)
                
                result = ac.checkDatabase()
                mock_logger.info.assert_called()
                log_calls = [str(call) for call in mock_logger.info.call_args_list]
                assert any("Database integrity check passed" in call for call in log_calls)


class TestSyncErrorHandling:
    def test_sync_auth_missing_key_error(self):
        with patch('app.core.SYNC_KEY', None):
            with pytest.raises(Exception, match="sync: key not configured"):
                ac._sync()

    def test_sync_collection_error_propagates(self, session_with_profile_loaded):
        with patch.object(ac, 'sync_auth') as mock_auth:
            mock_auth.return_value = Mock(hkey='test', endpoint=None, io_timeout_secs=10)
            
            with patch.object(ac.collection(), 'sync_collection', side_effect=SyncError("Network error")):
                with pytest.raises(SyncError, match="Network error"):
                    ac._sync()

    def test_full_sync_collection_reopen_error_handling(self, session_with_profile_loaded):
        with patch.object(ac, 'sync_auth') as mock_auth:
            mock_auth.return_value = Mock(hkey='test', endpoint=None, io_timeout_secs=10)
            
            with patch.object(ac.collection(), 'sync_collection') as mock_sync:
                with patch.object(ac.collection(), 'close_for_full_sync'):
                    with patch.object(ac.collection(), 'full_upload_or_download'):
                        with patch.object(ac.collection(), 'reopen', side_effect=Exception("Reopen failed")):
                            mock_output = Mock()
                            mock_output.NO_CHANGES = 0
                            mock_output.NORMAL_SYNC = 1
                            mock_output.FULL_SYNC_REQUIRED = 2
                            mock_output.required = mock_output.FULL_SYNC_REQUIRED
                            mock_output.server_media_usn = 123
                            mock_sync.return_value = mock_output
                            
                            with pytest.raises(Exception, match="Reopen failed"):
                                ac._sync(mode="upload")


class TestSyncLogging:
    def test_sync_status_logging(self, session_with_profile_loaded):
        with patch('app.core.logger') as mock_logger:
            with patch.object(ac, 'sync_auth') as mock_auth:
                mock_auth.return_value = Mock(hkey='test', endpoint=None, io_timeout_secs=10)
                
                with patch.object(ac.collection(), 'sync_collection') as mock_sync:
                    mock_output = Mock()
                    mock_output.NO_CHANGES = 0
                    mock_output.NORMAL_SYNC = 1
                    mock_output.required = mock_output.NO_CHANGES
                    
                    with patch.object(anki.sync.SyncOutput.ChangesRequired, 'Name') as mock_name:
                        mock_name.return_value = "NO_CHANGES"
                        mock_sync.return_value = mock_output
                        
                        ac._sync()
                        mock_logger.info.assert_called_with("Synced with status: NO_CHANGES")

    def test_sync_failure_logging(self, session_with_profile_loaded):
        with patch('app.core.logger') as mock_logger:
            with patch.object(ac, 'sync_auth') as mock_auth:
                mock_auth.return_value = Mock(hkey='test', endpoint=None, io_timeout_secs=10)
                
                with patch.object(ac.collection(), 'sync_collection') as mock_sync:
                    mock_output = Mock()
                    mock_output.NO_CHANGES = 0
                    mock_output.NORMAL_SYNC = 1
                    mock_output.FULL_SYNC_REQUIRED = 2
                    mock_output.required = mock_output.FULL_SYNC_REQUIRED
                    
                    with patch.object(anki.sync.SyncOutput.ChangesRequired, 'Name') as mock_name:
                        mock_name.return_value = "FULL_SYNC_REQUIRED"
                        mock_sync.return_value = mock_output
                        
                        with pytest.raises(Exception):
                            ac._sync()
                        
                        mock_logger.info.assert_called_with("Could not sync status FULL_SYNC_REQUIRED")