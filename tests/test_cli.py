import argparse
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest  # noqa

from app import server


class TestArgumentParsing:
    def test_parser_creation(self):
        parser = argparse.ArgumentParser(description="AnkiConnect server")
        parser.add_argument("--base", "-b", type=Path, help="base directory for the collection")
        parser.add_argument("--create", action="store_true", help="create a new collection if not present")
        
        # Test default arguments
        args = parser.parse_args([])
        assert args.base is None
        assert args.create is False

    def test_parser_with_base_directory(self):
        parser = argparse.ArgumentParser(description="AnkiConnect server")
        parser.add_argument("--base", "-b", type=Path, help="base directory for the collection")
        parser.add_argument("--create", action="store_true", help="create a new collection if not present")
        
        test_dir = "/tmp/test_collection"
        args = parser.parse_args(["--base", test_dir])
        assert args.base == Path(test_dir)
        assert args.create is False

    def test_parser_with_create_flag(self):
        parser = argparse.ArgumentParser(description="AnkiConnect server")
        parser.add_argument("--base", "-b", type=Path, help="base directory for the collection")
        parser.add_argument("--create", action="store_true", help="create a new collection if not present")
        
        args = parser.parse_args(["--create"])
        assert args.create is True

    def test_parser_short_form_arguments(self):
        parser = argparse.ArgumentParser(description="AnkiConnect server")
        parser.add_argument("--base", "-b", type=Path, help="base directory for the collection")
        parser.add_argument("--create", action="store_true", help="create a new collection if not present")
        
        test_dir = "/tmp/test"
        args = parser.parse_args(["-b", test_dir, "--create"])
        assert args.base == Path(test_dir)
        assert args.create is True


class TestServerStartup:
    def test_run_server_initialization(self):
        temp_dir = Path(tempfile.mkdtemp())
        
        with patch('app.server.AnkiConnectBridge') as mock_bridge:
            with patch('app.server.serve') as mock_serve:
                with patch('app.server.restart_periodic_sync') as mock_restart:
                    mock_bridge_instance = Mock()
                    mock_bridge_instance.sync_auth.return_value.endpoint = "test-endpoint"
                    mock_bridge.return_value = mock_bridge_instance
                    
                    server.run_server(temp_dir)
                    
                    mock_bridge.assert_called_once_with(temp_dir)
                    mock_restart.assert_called_once()
                    mock_serve.assert_called_once()

    def test_run_server_with_keyboard_interrupt(self):
        temp_dir = Path(tempfile.mkdtemp())
        
        with patch('app.server.AnkiConnectBridge') as mock_bridge:
            with patch('app.server.serve', side_effect=KeyboardInterrupt()):
                with patch('app.server.restart_periodic_sync'):
                    with patch('app.server.logger') as mock_logger:
                        mock_bridge_instance = Mock()
                        mock_bridge_instance.sync_auth.return_value.endpoint = None
                        mock_bridge.return_value = mock_bridge_instance
                        
                        server.run_server(temp_dir)
                        
                        mock_logger.info.assert_called_with("Server stopped by user")
                        mock_bridge_instance.close.assert_called_once()

    def test_run_server_with_exception(self):
        temp_dir = Path(tempfile.mkdtemp())
        
        with patch('app.server.AnkiConnectBridge') as mock_bridge:
            with patch('app.server.serve', side_effect=Exception("Server error")):
                with patch('app.server.restart_periodic_sync'):
                    with patch('app.server.logger') as mock_logger:
                        mock_bridge_instance = Mock()
                        mock_bridge_instance.sync_auth.return_value.endpoint = None
                        mock_bridge.return_value = mock_bridge_instance
                        
                        server.run_server(temp_dir)
                        
                        mock_logger.error.assert_called()
                        mock_bridge_instance.close.assert_called_once()

    def test_run_server_cleanup_timers(self):
        temp_dir = Path(tempfile.mkdtemp())
        
        with patch('app.server.AnkiConnectBridge') as mock_bridge:
            with patch('app.server.serve'):
                with patch('app.server.restart_periodic_sync'):
                    sync_timer = Mock()
                    periodic_timer = Mock()
                    server.sync_after_mod_timer = sync_timer
                    server.sync_periodic_timer = periodic_timer
                    
                    mock_bridge_instance = Mock()
                    mock_bridge_instance.sync_auth.return_value.endpoint = None
                    mock_bridge.return_value = mock_bridge_instance
                    
                    server.run_server(temp_dir)
                    
                    sync_timer.cancel.assert_called_once()
                    periodic_timer.cancel.assert_called_once()

    def test_run_server_sync_endpoint_logging(self):
        temp_dir = Path(tempfile.mkdtemp())
        
        with patch('app.server.AnkiConnectBridge') as mock_bridge:
            with patch('app.server.serve'):
                with patch('app.server.restart_periodic_sync'):
                    with patch('app.server.logger') as mock_logger:
                        mock_bridge_instance = Mock()
                        mock_bridge_instance.sync_auth.return_value.endpoint = "https://sync.example.com"
                        mock_bridge.return_value = mock_bridge_instance
                        
                        server.run_server(temp_dir)
                        
                        log_calls = [str(call) for call in mock_logger.info.call_args_list]
                        assert any("https://sync.example.com" in call for call in log_calls)

    def test_run_server_ankiweb_default_logging(self):
        temp_dir = Path(tempfile.mkdtemp())
        
        with patch('app.server.AnkiConnectBridge') as mock_bridge:
            with patch('app.server.serve'):
                with patch('app.server.restart_periodic_sync'):
                    with patch('app.server.logger') as mock_logger:
                        mock_bridge_instance = Mock()
                        mock_bridge_instance.sync_auth.return_value.endpoint = None
                        mock_bridge.return_value = mock_bridge_instance
                        
                        server.run_server(temp_dir)
                        
                        log_calls = [str(call) for call in mock_logger.info.call_args_list]
                        assert any("AnkiWeb" in call for call in log_calls)


class TestMainExecution:
    def test_main_with_no_base_directory(self):
        with patch('app.server.ANKI_BASE_DIR', None):
            with patch('app.server.logger') as mock_logger:
                with patch('sys.exit') as mock_exit:
                    with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                        mock_parse.return_value = argparse.Namespace(base=None, create=False)
                        
                        # Import and execute the main logic
                        import sys
                        from unittest import mock
                        
                        original_argv = sys.argv
                        try:
                            sys.argv = ['server.py']
                            with mock.patch('app.server.__name__', '__main__'):
                                exec(compile(open('app/server.py').read(), 'app/server.py', 'exec'))
                        except SystemExit:
                            pass
                        finally:
                            sys.argv = original_argv
                        
                        mock_logger.error.assert_called()
                        mock_exit.assert_called_with(1)

    def test_main_with_non_existent_directory(self):
        with patch('app.server.logger') as mock_logger:
            with patch('sys.exit') as mock_exit:
                with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                    mock_parse.return_value = argparse.Namespace(
                        base=Path("/non/existent/path"), 
                        create=False
                    )
                    
                    import sys
                    from unittest import mock
                    
                    original_argv = sys.argv
                    try:
                        sys.argv = ['server.py', '--base', '/non/existent/path']
                        with mock.patch('app.server.__name__', '__main__'):
                            exec(compile(open('app/server.py').read(), 'app/server.py', 'exec'))
                    except SystemExit:
                        pass
                    finally:
                        sys.argv = original_argv
                    
                    mock_logger.error.assert_called()
                    mock_exit.assert_called_with(1)

    def test_main_with_missing_collection_file(self):
        temp_dir = Path(tempfile.mkdtemp())
        
        with patch('app.server.logger') as mock_logger:
            with patch('sys.exit') as mock_exit:
                with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                    mock_parse.return_value = argparse.Namespace(
                        base=temp_dir, 
                        create=False
                    )
                    
                    import sys
                    from unittest import mock
                    
                    original_argv = sys.argv
                    try:
                        sys.argv = ['server.py', '--base', str(temp_dir)]
                        with mock.patch('app.server.__name__', '__main__'):
                            exec(compile(open('app/server.py').read(), 'app/server.py', 'exec'))
                    except SystemExit:
                        pass
                    finally:
                        sys.argv = original_argv
                    
                    mock_logger.error.assert_called()
                    mock_exit.assert_called_with(1)

    def test_api_key_logging(self):
        with patch('app.server.API_KEY', 'test-key'):
            with patch('app.server.logger') as mock_logger:
                with patch('app.server.run_server') as mock_run:
                    with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                        temp_dir = Path(tempfile.mkdtemp())
                        collection_file = temp_dir / "collection.anki2"
                        collection_file.touch()
                        
                        mock_parse.return_value = argparse.Namespace(
                            base=temp_dir, 
                            create=False
                        )
                        
                        import sys
                        from unittest import mock
                        
                        original_argv = sys.argv
                        try:
                            sys.argv = ['server.py', '--base', str(temp_dir)]
                            with mock.patch('app.server.__name__', '__main__'):
                                exec(compile(open('app/server.py').read(), 'app/server.py', 'exec'))
                        except SystemExit:
                            pass
                        finally:
                            sys.argv = original_argv
                        
                        log_calls = [str(call) for call in mock_logger.info.call_args_list]
                        assert any("API key authentication enabled" in call for call in log_calls)

    def test_no_api_key_warning(self):
        with patch('app.server.API_KEY', None):
            with patch('app.server.logger') as mock_logger:
                with patch('app.server.run_server') as mock_run:
                    with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                        temp_dir = Path(tempfile.mkdtemp())
                        collection_file = temp_dir / "collection.anki2"
                        collection_file.touch()
                        
                        mock_parse.return_value = argparse.Namespace(
                            base=temp_dir, 
                            create=False
                        )
                        
                        import sys
                        from unittest import mock
                        
                        original_argv = sys.argv
                        try:
                            sys.argv = ['server.py', '--base', str(temp_dir)]
                            with mock.patch('app.server.__name__', '__main__'):
                                exec(compile(open('app/server.py').read(), 'app/server.py', 'exec'))
                        except SystemExit:
                            pass
                        finally:
                            sys.argv = original_argv
                        
                        log_calls = [str(call) for call in mock_logger.warning.call_args_list]
                        assert any("consider setting ANKICONNECT_API_KEY" in call for call in log_calls)