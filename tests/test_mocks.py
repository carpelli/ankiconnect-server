import sys
from unittest.mock import patch

import pytest  # noqa

from app.gui_stubs import MinimalMock, MockQt, MockQMessageBox, MockGuiHooks, MockAqt, install_gui_stubs, create_mock_module
from app.anki_mocks import MockProfileManager, MockProgress, MockAddonManager, MockAnkiMainWindow


class TestMinimalMock:
    def test_minimal_mock_instantiation(self):
        mock = MinimalMock()
        assert isinstance(mock, MinimalMock)

    def test_minimal_mock_attribute_access(self):
        mock = MinimalMock()
        attr = mock.some_attribute
        assert isinstance(attr, MinimalMock)

    def test_minimal_mock_method_call(self):
        mock = MinimalMock()
        result = mock.some_method("arg1", kwarg="value")
        assert isinstance(result, MinimalMock)

    def test_minimal_mock_bool_conversion(self):
        mock = MinimalMock()
        assert bool(mock) is True

    def test_minimal_mock_string_representation(self):
        mock = MinimalMock()
        str_repr = str(mock)
        assert "MinimalMock" in str_repr

    def test_minimal_mock_contains_operator(self):
        mock = MinimalMock()
        assert "anything" in mock

    def test_minimal_mock_list_methods(self):
        mock = MinimalMock()
        # Should not raise exceptions
        mock.append("item")
        mock.remove("item")


class TestMockQt:
    def test_mock_qt_sort_order(self):
        qt = MockQt()
        assert hasattr(qt.SortOrder, 'AscendingOrder')
        assert hasattr(qt.SortOrder, 'DescendingOrder')

    def test_mock_qt_window_type(self):
        qt = MockQt()
        assert hasattr(qt.WindowType, 'Widget')
        assert hasattr(qt.WindowType, 'Window')
        assert hasattr(qt.WindowType, 'Dialog')

    def test_mock_qt_key(self):
        qt = MockQt()
        assert hasattr(qt, 'Key')


class TestMockQMessageBox:
    def test_message_box_icons(self):
        box = MockQMessageBox()
        assert hasattr(box.Icon, 'Critical')
        assert hasattr(box.Icon, 'Warning')
        assert hasattr(box.Icon, 'Information')

    def test_message_box_buttons(self):
        box = MockQMessageBox()
        assert hasattr(box.StandardButton, 'Ok')
        assert hasattr(box.StandardButton, 'Cancel')
        assert hasattr(box.StandardButton, 'Yes')
        assert hasattr(box.StandardButton, 'No')

    def test_message_box_exec(self):
        box = MockQMessageBox()
        result = box.exec()
        assert result == 1  # Should return Ok button value

    def test_message_box_critical_static_method(self):
        # Should not raise an exception
        MockQMessageBox.critical(None, "Error", "Test error message")


class TestMockGuiHooks:
    def test_gui_hooks_initialization(self):
        hooks = MockGuiHooks()
        expected_hooks = [
            'card_layout_will_show', 'card_will_show', 'reviewer_did_show_question',
            'reviewer_did_show_answer', 'state_did_change', 'reviewer_will_end'
        ]
        
        for hook in expected_hooks:
            assert hasattr(hooks, hook)

    def test_gui_hooks_attribute_access(self):
        hooks = MockGuiHooks()
        hook = hooks.some_custom_hook
        assert isinstance(hook, MinimalMock)


class TestMockAqt:
    def test_mock_aqt_initialization(self):
        aqt = MockAqt()
        
        expected_modules = ['qt', 'utils', 'gui_hooks', 'operations']
        for module_name in expected_modules:
            assert hasattr(aqt, module_name)

    def test_mock_aqt_qt_module(self):
        aqt = MockAqt()
        assert isinstance(aqt.qt, MockQt)

    def test_mock_aqt_qmessagebox(self):
        aqt = MockAqt()
        assert hasattr(aqt, 'QMessageBox')
        assert isinstance(aqt.QMessageBox, type(MockQMessageBox))

    def test_mock_aqt_gui_hooks(self):
        aqt = MockAqt()
        assert isinstance(aqt.gui_hooks, MockGuiHooks)


class TestCreateMockModule:
    def test_create_basic_mock_module(self):
        mock_module = create_mock_module("test_module")
        assert hasattr(mock_module, '__name__')
        assert mock_module.__name__ == 'test_module'

    def test_create_mock_module_with_attributes(self):
        mock_module = create_mock_module("test_module", attr1="value1", attr2=42)
        assert mock_module.attr1 == "value1"
        assert mock_module.attr2 == 42


class TestInstallGuiStubs:
    def test_install_gui_stubs_modifies_sys_modules(self):
        original_modules = dict(sys.modules)
        
        try:
            result = install_gui_stubs()
            
            # Check that aqt module is installed
            assert 'aqt' in sys.modules
            assert isinstance(result, MockAqt)
            
            # Check some expected submodules
            expected_modules = ['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui']
            for module_name in expected_modules:
                assert module_name in sys.modules
                
        finally:
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)

    def test_install_gui_stubs_returns_mock_aqt(self):
        original_modules = dict(sys.modules)
        
        try:
            result = install_gui_stubs()
            assert isinstance(result, MockAqt)
        finally:
            sys.modules.clear()
            sys.modules.update(original_modules)


class TestMockProfileManager:
    def test_profile_manager_initialization(self):
        pm = MockProfileManager()
        assert pm.name == "test_user"

    def test_profile_manager_profiles(self):
        pm = MockProfileManager()
        profiles = pm.profiles()
        assert profiles == ["test_user"]

    def test_profile_manager_attribute_access(self):
        pm = MockProfileManager()
        attr = pm.some_attribute
        assert isinstance(attr, MinimalMock)


class TestMockProgress:
    def test_progress_update(self):
        progress = MockProgress()
        # Should not raise exceptions
        progress.update("Loading...", 50)
        progress.update(label="Processing...")
        progress.update(value=75)

    def test_progress_lifecycle(self):
        progress = MockProgress()
        # Should not raise exceptions
        progress.start(max=100)
        progress.update("Working...", 25)
        progress.finish()


class TestMockAddonManager:
    def test_addon_manager_get_config(self):
        manager = MockAddonManager()
        config = manager.getConfig("test_addon")
        assert config == {}

    def test_addon_manager_write_config(self):
        manager = MockAddonManager()
        # Should not raise exceptions
        manager.writeConfig("test_addon", {"key": "value"})


class TestMockAnkiMainWindow:
    def test_main_window_initialization(self):
        mw = MockAnkiMainWindow("/path/to/collection.anki2")
        assert mw.col is not None
        assert isinstance(mw.pm, MockProfileManager)
        assert isinstance(mw.progress, MockProgress)
        assert isinstance(mw.addonManager, MockAddonManager)

    def test_main_window_methods(self):
        mw = MockAnkiMainWindow("/path/to/collection.anki2")
        
        # Should not raise exceptions
        mw.requireReset()
        mw.reset()
        mw.unloadProfileAndShowProfileManager()
        
        # Test return values
        assert mw.isVisible() is True

    def test_main_window_close(self):
        mw = MockAnkiMainWindow("/path/to/collection.anki2")
        
        with patch.object(mw.col, 'close') as mock_close:
            mw.close()
            mock_close.assert_called_once()


class TestMockIntegration:
    def test_mocks_work_together(self):
        # Test that the mocks integrate properly
        with patch.dict(sys.modules, {}, clear=True):
            aqt = install_gui_stubs()
            mw = MockAnkiMainWindow("/test/collection.anki2")
            
            # Should be able to access GUI components through mocks
            assert hasattr(aqt, 'QMessageBox')
            assert hasattr(aqt, 'gui_hooks')
            assert isinstance(mw.progress, MockProgress)
            
            # Should be able to call methods without errors
            aqt.QMessageBox.critical(None, "Test", "Message")
            mw.progress.update("Testing...", 50)
            mw.requireReset()