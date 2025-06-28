import logging
from typing import Optional
from typing_extensions import TYPE_CHECKING
import sys

import anki.lang
import anki.collection # fix anki circular import
anki.lang.set_lang('en_US') # TODO: Implement language selection

from app.config import get_config

# Import GUI stubs before importing anything that uses aqt
from app.anki_mocks import MockAnkiMainWindow, find_collection_path
from app.gui_stubs import install_gui_stubs
install_gui_stubs()

import aqt # type: ignore

sys.path.append('libs/ankiconnect')
if TYPE_CHECKING:
    from libs.ankiconnect.plugin import AnkiConnect
else:
    from plugin import AnkiConnect # to avoid code execution on import
sys.path.remove('libs/ankiconnect')

logger = logging.getLogger(__name__)

class AnkiConnectBridge:
    """
    Bridge that wraps the existing AnkiConnect plugin.
    
    This class provides a minimal interface to the AnkiConnect plugin,
    handling the setup of mock Anki environment and request processing.
    """

    def __init__(self, collection_path: Optional[str] = None):
        """
        Initialize the AnkiConnect bridge.
        
        Args:
            collection_path: Optional path to Anki collection. If not provided,
                           will use config or auto-detect default location.
        """

        # Set up the mock Anki environment
        self.collection_path = collection_path or get_config()['collection_path'] or find_collection_path()
        logger.info(f"Initializing bridge with collection: {self.collection_path}")
        
        self.mock_mw = MockAnkiMainWindow(self.collection_path)

        # Patch aqt.mw to point to our mock
        aqt.mw = self.mock_mw
        self.ankiconnect = AnkiConnect()

        # Initialize logging if needed
        try:
            self.ankiconnect.initLogging()
            logger.debug("AnkiConnect logging initialized")
        except Exception as e:
            logger.warning(f"Could not initialize AnkiConnect logging: {e}")

        logger.info("AnkiConnect bridge initialized successfully")

    def handle_request(self, request_data: dict) -> dict:
        """
        Process an AnkiConnect request using the original plugin.
        
        Args:
            request_data: The request data from the client
            
        Returns:
            Response data in AnkiConnect format
        """
        if request_data.get('action') == 'requestPermission':
            return self.ankiconnect.requestPermission(origin='', allowed=True)
        return self.ankiconnect.handler(request_data)

    def close(self) -> None:
        """Clean up resources and close the Anki collection."""
        try:
            if hasattr(self, 'mock_mw'):
                self.mock_mw.close()
                logger.info("Bridge resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
