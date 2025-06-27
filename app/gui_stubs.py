"""
Simplified GUI stubs to replace aqt dependencies.
These stubs provide just enough functionality to allow imports and basic instantiation,
while GUI method requests fail gracefully at the API level.
"""

import logging
import sys
from types import ModuleType
from typing import Any, Union

logger = logging.getLogger(__name__)


class MinimalMock:
    """Base class for minimal mocks that can be instantiated and have basic attributes"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def __getattr__(self, name: str) -> 'MinimalMock':
        """Return another MinimalMock for any attribute access"""
        return MinimalMock()

    def __call__(self, *args: Any, **kwargs: Any) -> 'MinimalMock':
        """Allow the mock to be called - just return self for chaining"""
        return MinimalMock()

    def __bool__(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"MinimalMock({self.__class__.__name__})"

    def __contains__(self, item: Any) -> bool:
        """Support 'in' operator - always return False for membership tests"""
        return False

    def append(self, *args: Any, **kwargs: Any) -> None:
        """Handle list-like operations (e.g., hook registration)"""
        pass

    def remove(self, *args: Any, **kwargs: Any) -> None:
        """Handle list-like operations"""
        pass


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
    """Mock QMessageBox with essential constants"""

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

    def exec(self) -> int:
        """Always return "No" to deny permissions by default"""
        return self.StandardButton.No

    @staticmethod
    def critical(parent: Any, title: str, message: str) -> None:
        """Log critical messages instead of showing dialog"""
        logger.error(f"QMessageBox.critical: {title}: {message}")


class MockGuiHooks:
    """Simplified mock gui_hooks module"""

    def __init__(self) -> None:
        # Initialize common hooks as MinimalMock instances
        self.browser_will_search = MinimalMock()
        self.browser_did_change_row = MinimalMock()
        self.operation_did_execute = MinimalMock()
        self.editor_did_load_note = MinimalMock()
        self.editor_did_init = MinimalMock()
        self.editor_did_init_buttons = MinimalMock()

    def __getattr__(self, name: str) -> MinimalMock:
        """Return a MinimalMock for any hook not explicitly defined"""
        return MinimalMock()


def create_mock_module(name: str, **attrs) -> Any:
    """Helper function to create mock modules"""
    return type(name, (), attrs)()


class MockAqt:
    """Simplified mock aqt module"""

    def __init__(self) -> None:
        self.appVersion = "25.2.6"
        self.mw = None  # Will be set by anki_mocks.setup_anki_environment()
        self.dialogs = MinimalMock()
        self.gui_hooks = MockGuiHooks()
        
        # Create minimal submodules
        self.utils = MinimalMock()
        self.editor = MinimalMock()
        self.forms = MinimalMock()
        self.import_export = MinimalMock()
        
        # Create Qt submodule
        self.qt = create_mock_module('MockQtModule',
            Qt=MockQt,
            QTimer=MinimalMock,
            QMessageBox=MockQMessageBox,
            QCheckBox=MinimalMock,
            QKeySequence=MinimalMock,
            QShortcut=MinimalMock,
            QCloseEvent=MinimalMock,
            QMainWindow=MinimalMock,
        )

        # Create previewer module first
        self._previewer_module = create_mock_module('PreviewerModule',
            MultiCardPreviewer=MinimalMock
        )
        
        # Create browser submodule with previewer
        self.browser = create_mock_module('BrowserModule',
            previewer=self._previewer_module
        )

        # Create editcurrent submodule
        self.editcurrent = create_mock_module('EditCurrentModule',
            EditCurrent=MinimalMock
        )


def install_gui_stubs() -> Union[MockAqt, ModuleType]:
    """
    Install simplified GUI stubs by patching sys.modules.
    
    Returns:
        The mock aqt module instance
    """
    if 'aqt' in sys.modules:
        logger.debug("aqt module already exists, returning existing instance")
        return sys.modules['aqt']

    # Create mock aqt module
    mock_aqt = MockAqt()

    # Install main modules
    sys.modules['aqt'] = mock_aqt  # type: ignore
    sys.modules['aqt.qt'] = mock_aqt.qt  # type: ignore
    sys.modules['aqt.editor'] = mock_aqt.editor  # type: ignore
    sys.modules['aqt.editcurrent'] = mock_aqt.editcurrent  # type: ignore
    sys.modules['aqt.forms'] = mock_aqt.forms  # type: ignore
    sys.modules['aqt.browser'] = mock_aqt.browser  # type: ignore
    sys.modules['aqt.browser.previewer'] = mock_aqt._previewer_module  # type: ignore
    sys.modules['aqt.utils'] = mock_aqt.utils  # type: ignore
    sys.modules['aqt.import_export'] = mock_aqt.import_export  # type: ignore
    sys.modules['aqt.gui_hooks'] = mock_aqt.gui_hooks  # type: ignore

    return mock_aqt


# Auto-install stubs when this module is imported
if 'aqt' not in sys.modules:
    install_gui_stubs()
