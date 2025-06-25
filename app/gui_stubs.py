"""
Minimal GUI stubs to replace aqt dependencies.
These stubs provide just enough functionality to allow imports and basic instantiation,
while GUI method requests fail gracefully at the API level.
"""

import sys
from unittest.mock import MagicMock


class MinimalMock:
    """Base class for minimal mocks that can be instantiated and have basic attributes"""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        # Return another MinimalMock for any attribute access
        return MinimalMock()

    def __call__(self, *args, **kwargs):
        # Allow the mock to be called - just return self for chaining
        return MinimalMock()

    def __bool__(self):
        return True

    def __str__(self):
        return f"MinimalMock({self.__class__.__name__})"

    def append(self, *args, **kwargs):
        """Handle list-like operations (e.g., hook registration)"""
        pass

    def remove(self, *args, **kwargs):
        """Handle list-like operations"""
        pass


class InheritableMock:
    """Mock class that can be inherited from"""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return MinimalMock()


class MockQt:
    """Mock Qt constants - only what's actually referenced"""

    class SortOrder:
        AscendingOrder = 0
        DescendingOrder = 1

    class WindowType:
        Window = 1
        WindowStaysOnTopHint = 0x00040000

    # Direct constants for Qt5 compatibility
    WindowStaysOnTopHint = 0x00040000


class MockQMessageBox(MinimalMock):
    """Mock QMessageBox - just needs the constants for comparisons"""

    class Icon:
        Question = 4
        Information = 1
        Warning = 2
        Critical = 3

    class StandardButton:
        Yes = 0x00004000
        No = 0x00010000
        Ok = 0x00000400
        Cancel = 0x00400000

    def exec(self):
        # Always return "No" to deny permissions by default
        return self.StandardButton.No

    @staticmethod
    def critical(parent, title, message):
        # Just print instead of showing dialog
        print(f"ERROR: {title}: {message}")


# Note: Anki-specific mocks moved to anki_mocks.py
# This file now contains only Qt/GUI components


class MockDialogs:
    """Mock dialogs system"""

    def __init__(self):
        self._dialogs = {}

    def open(self, dialog_name, *args, **kwargs):
        return MinimalMock()

    def register_dialog(self, tag, dialog_class):
        self._dialogs[tag] = (dialog_class, None)

    def markClosed(self, tag):
        pass


class MockGuiHooks:
    """Mock gui_hooks module with proper hook registration"""

    def __init__(self):
        self.browser_will_search = MinimalMock()
        self.browser_did_change_row = MinimalMock()
        self.operation_did_execute = MinimalMock()
        self.editor_did_load_note = MinimalMock()
        self.editor_did_init = MinimalMock()
        self.editor_did_init_buttons = MinimalMock()

    def __getattr__(self, name):
        # Return a MinimalMock for any hook not explicitly defined
        return MinimalMock()


class MockAqt:
    """Main mock aqt module"""

    def __init__(self):
        self.appVersion = "25.2.6"
        self.mw = None  # Will be set by anki_mocks.setup_anki_environment()
        self.dialogs = MockDialogs()

        # All other attributes return MinimalMock
        self.gui_hooks = MockGuiHooks()
        self.utils = MinimalMock()
        self.editor = MinimalMock()
        self.editcurrent = type('EditCurrentModule', (), {'EditCurrent': InheritableMock})()
        self.forms = MinimalMock()
        self.browser = type('BrowserModule', (), {
            'previewer': type('PreviewerModule', (), {
                'MultiCardPreviewer': InheritableMock
            })()
        })()
        self.import_export = MinimalMock()

        # Qt submodule with essential components
        self.qt = type('MockQtModule', (), {
            'Qt': MinimalMock,
            'QTimer': MinimalMock,
            'QMessageBox': MockQMessageBox,
            'QCheckBox': MinimalMock,
            'QKeySequence': MinimalMock,
            'QShortcut': MinimalMock,
            'QCloseEvent': MinimalMock,
            'QMainWindow': MinimalMock,
        })()


def install_gui_stubs():
    """Install minimal GUI stubs by patching sys.modules"""

    if 'aqt' in sys.modules:
        return sys.modules['aqt']

    # Create mock aqt module
    mock_aqt = MockAqt()

    # Install main modules
    sys.modules['aqt'] = mock_aqt
    sys.modules['aqt.qt'] = mock_aqt.qt
    sys.modules['aqt.editor'] = mock_aqt.editor
    sys.modules['aqt.editcurrent'] = mock_aqt.editcurrent
    sys.modules['aqt.forms'] = mock_aqt.forms
    sys.modules['aqt.forms.editcurrent'] = mock_aqt.forms
    sys.modules['aqt.browser'] = mock_aqt.browser
    sys.modules['aqt.browser.previewer'] = mock_aqt.browser
    sys.modules['aqt.utils'] = mock_aqt.utils
    sys.modules['aqt.import_export'] = mock_aqt.import_export
    sys.modules['aqt.import_export.importing'] = mock_aqt.import_export
    sys.modules['aqt.gui_hooks'] = mock_aqt.gui_hooks

    return mock_aqt


# Auto-install stubs when this module is imported
if 'aqt' not in sys.modules:
    install_gui_stubs()
