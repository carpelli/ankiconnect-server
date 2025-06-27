import logging
from typing import Optional
from typing_extensions import TYPE_CHECKING
import sys

import anki.lang

from app.config import get_config

# Import GUI stubs before importing anything that uses aqt
from .gui_stubs import install_gui_stubs
install_gui_stubs()

from .anki_mocks import MockAnkiMainWindow, find_collection_path

logger = logging.getLogger(__name__)

import aqt # type: ignore

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
        anki.lang.set_lang('en') # TODO: Implement language selection

        # Set up the mock Anki environment
        self.collection_path = collection_path or get_config()['collection_path'] or find_collection_path()
        logger.info(f"Initializing bridge with collection: {self.collection_path}")
        
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
            logger.debug("AnkiConnect logging initialized")
        except Exception as e:
            logger.warning(f"Could not initialize AnkiConnect logging: {e}")

        logger.info("AnkiConnect bridge initialized successfully")

    def process_request(self, request_data: dict) -> dict:
        """
        Process an AnkiConnect request using the original plugin.
        
        Args:
            request_data: The request data from the client
            
        Returns:
            Response data in AnkiConnect format
        """
        try:
            logger.debug(f"Processing request: {request_data.get('action', 'unknown')}")
            # Use the original AnkiConnect handler
            result = self.ankiconnect.handler(request_data)
            logger.debug(f"Request processed successfully: {request_data.get('action', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"Error processing request {request_data.get('action', 'unknown')}: {e}", exc_info=True)
            # Return error in AnkiConnect format
            return {"result": None, "error": str(e)}

    def close(self) -> None:
        """Clean up resources and close the Anki collection."""
        try:
            if hasattr(self, 'mock_mw'):
                self.mock_mw.close()
                logger.info("Bridge resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __enter__(self):
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point with automatic cleanup."""
        self.close()
