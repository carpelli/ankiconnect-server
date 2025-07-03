import logging
from typing_extensions import TYPE_CHECKING
import sys
from pathlib import Path

import anki.lang
import anki.sync
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
    from libs.ankiconnect.plugin import AnkiConnect, util
else:
    from plugin import AnkiConnect, util # to avoid code execution on import
sys.path.remove('libs/ankiconnect')

logger = logging.getLogger(__name__)

class AnkiConnectBridge(AnkiConnect):
    """
    Bridge that wraps the existing AnkiConnect plugin.

    This class provides a minimal interface to the AnkiConnect plugin,
    handling the setup of mock Anki environment and request processing.
    """

    _sync_auth: anki.sync.SyncAuth | None

    def __init__(self, collection_path: str | None = None):
        # Set up the mock Anki environment
        self.collection_path = collection_path or get_config()['collection_path'] or find_collection_path()
        logger.info(f"Initializing with collection: {Path(self.collection_path).absolute()}")

        self.mock_mw = MockAnkiMainWindow(self.collection_path)
        # Patch aqt.mw to point to our mock
        aqt.mw = self.mock_mw

        # Initialize logging if needed
        try:
            self.initLogging()
            logger.debug("AnkiConnect logging initialized")
        except Exception as e:
            logger.warning(f"Could not initialize AnkiConnect logging: {e}")

        logger.info("AnkiConnect bridge initialized successfully")

    def handler(self, request: dict) -> dict:
        """
        Process an AnkiConnect request using the original plugin.

        Args:
            request_data: The request data from the client

        Returns:
            Response data in AnkiConnect format
        """
        if request.get('action') == 'requestPermission':
            return self.requestPermission(origin='', allowed=True)
        return super().handler(request)

    def sync_auth(self) -> anki.sync.SyncAuth:
        if (hkey := get_config()['sync_key']) is None:
            raise Exception("sync: key not configured")
        return anki.sync.SyncAuth(
            hkey=hkey,
            endpoint=get_config()['sync_endpoint'],
            io_timeout_secs=10 # TODO configure?
        )

    def _sync(self, mode: str | None = None):
        auth = self.sync_auth()
        col = self.collection()
        out = col.sync_collection(auth, True) # TODO media enabled option
        accepted_sync_statuses = [out.NO_CHANGES, out.NORMAL_SYNC]
        status_str = anki.sync.SyncOutput.ChangesRequired.Name(out.required)
        if out.required not in accepted_sync_statuses:
            if mode in ['download', 'upload']:
                col.close_for_full_sync() # should reopen automatically
                col.full_upload_or_download(auth=auth, server_usn=out.server_media_usn, upload=(mode=='upload')) # TODO media enabled option
            else:
                logger.info(f"Could not sync status {status_str}")
                raise Exception(f"could not sync status {status_str} - use fullSync")
        logger.info(f"Synced with status: {status_str}")

    @util.api()
    def sync(self):
        self._sync()

    @util.api()
    def fullSync(self, mode: str):
        self._sync(mode=mode)

    def close(self) -> None:
        """Clean up resources and close the Anki collection."""
        try:
            if hasattr(self, 'mock_mw'):
                self.mock_mw.close()
                logger.info("Bridge resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
