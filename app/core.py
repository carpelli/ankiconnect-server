from typing import Optional
from typing_extensions import TYPE_CHECKING
import sys

# Import GUI stubs before importing anything that uses aqt
from .gui_stubs import install_gui_stubs
install_gui_stubs()

from .anki_mocks import MockAnkiMainWindow, find_collection_path

import aqt #type: ignore

class AnkiConnectBridge:
    """
    Minimal bridge that wraps the existing AnkiConnect plugin
    """

    def __init__(self, collection_path: Optional[str] = None):
        # Set up the mock Anki environment
        self.collection_path = collection_path or find_collection_path()
        self.mock_mw = MockAnkiMainWindow(self.collection_path)

        # Patch aqt.mw to point to our mock
        aqt.mw = self.mock_mw

        sys.path.append('libs/ankiconnect')
        if TYPE_CHECKING:
            from libs.ankiconnect.plugin import AnkiConnect
        else:
            from plugin import AnkiConnect
        self.ankiconnect = AnkiConnect()

        # Initialize logging if needed
        try:
            self.ankiconnect.initLogging()
        except:
            pass

    def process_request(self, request_data: dict) -> dict:
        """Process an AnkiConnect request using the original plugin"""
        try:
            # Use the original AnkiConnect handler
            return self.ankiconnect.handler(request_data)
        except Exception as e:
            # Return error in AnkiConnect format
            return {"result": None, "error": str(e)}

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'mock_mw'):
            self.mock_mw.close
