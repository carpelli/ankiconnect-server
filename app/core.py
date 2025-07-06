import logging
from pathlib import Path

import anki.sync

from app.anki_mocks import MockAnkiMainWindow
from app.config import ANKI_BASE_DIR, SYNC_ENDPOINT, SYNC_KEY
from app.plugin import AnkiConnect, util

# must be imported after app.plugin, which installs aqt stubs
import aqt  # type: ignore # isort: skip

logger = logging.getLogger(__name__)


class AnkiConnectBridge(AnkiConnect):
    """
    Bridge that wraps the existing AnkiConnect plugin.

    This class provides a minimal interface to the AnkiConnect plugin,
    handling the setup of mock Anki environment and request processing.
    """

    _sync_auth: anki.sync.SyncAuth | None

    def __init__(self, base_dir: Path):
        self.collection_path = str(base_dir.absolute() / "collection.anki2")
        logger.info(f"Initializing with collection: {self.collection_path}")

        self.mock_mw = MockAnkiMainWindow(self.collection_path)
        # Patch aqt.mw to point to our mock
        aqt.mw = self.mock_mw
        self.log = None

        logger.info("AnkiConnect bridge initialized successfully")

    def handler(self, request: dict) -> dict:
        """
        Process an AnkiConnect request using the original plugin.

        Args:
            request_data: The request data from the client

        Returns:
            Response data in AnkiConnect format
        """
        if request.get("action") == "requestPermission":
            return self.requestPermission(origin="", allowed=True)
        return super().handler(request)

    def sync_auth(self) -> anki.sync.SyncAuth:
        if (hkey := SYNC_KEY) is None:
            raise Exception("sync: key not configured")
        return anki.sync.SyncAuth(
            hkey=hkey,
            endpoint=SYNC_ENDPOINT,
            io_timeout_secs=10,  # TODO configure?
        )

    def _sync(self, mode: str | None = None):
        auth = self.sync_auth()
        col = self.collection()
        out = col.sync_collection(auth, True)  # TODO media enabled option
        accepted_sync_statuses = [out.NO_CHANGES, out.NORMAL_SYNC]
        status_str = anki.sync.SyncOutput.ChangesRequired.Name(out.required)
        if out.required not in accepted_sync_statuses:
            if mode in ["download", "upload"]:
                col.close_for_full_sync()
                col.full_upload_or_download(
                    auth=auth,
                    server_usn=out.server_media_usn,
                    upload=(mode == "upload"),
                )  # TODO media enabled option
                col.reopen()
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

    @util.api()
    def checkDatabase(self):
        problems, ok = self.collection().fix_integrity()
        if ok:
            logger.info("Database integrity check passed")
        else:
            logger.error("Database integrity check failed")
        for problem in problems.split("\n"):
            if problem.strip():
                (logger.info if ok else logger.error)(problem)
        return {"problems": problems, "ok": ok}

    def close(self):
        """Clean up resources and close the Anki collection."""
        try:
            if hasattr(self, "mock_mw"):
                self.mock_mw.close()
                logger.info("Bridge resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
