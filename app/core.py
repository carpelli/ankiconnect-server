import logging
import os
from pathlib import Path

import anki.collection
import anki.sync
import anki.utils

from app.anki_mocks import MockAnkiMainWindow
from app.config import SYNC_ENDPOINT, SYNC_KEY, get_ankiconnect_config
from app.plugin import AnkiConnect, util, web

# must be imported after app.plugin, which installs aqt stubs
import aqt  # type: ignore # isort: skip

logger = logging.getLogger(__name__)


# Set platform environment variable for sync protocol (like aqt)
os.environ["PLATFORM"] = anki.utils.plat_desc()


class AnkiConnectBridge(AnkiConnect):
    """
    Bridge that wraps the existing AnkiConnect plugin.

    This class provides a minimal interface to the AnkiConnect plugin,
    handling the setup of mock Anki environment and request processing.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
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
            return_value = self.requestPermission(origin="", allowed=True)
            return web.format_success_reply(
                get_ankiconnect_config()["apiVersion"], return_value
            )
        return super().handler(request)

    _current_sync_url = None

    def sync_auth(self) -> anki.sync.SyncAuth:
        if (hkey := SYNC_KEY) is None:
            raise Exception("sync: key not configured")
        return anki.sync.SyncAuth(
            hkey=hkey,
            endpoint=self._current_sync_url or SYNC_ENDPOINT,
            io_timeout_secs=10,  # TODO configure?
        )

    def _sync(self, mode: str | None = None):
        auth = self.sync_auth()
        col = self.collection()
        logger.debug(f"Starting sync operation, mode={mode}")
        out = col.sync_collection(auth, True)  # TODO media enabled option
        if out.new_endpoint:
            logger.info(f"Sync - New endpoint requested: {out.new_endpoint}")
            self._current_sync_url = out.new_endpoint
        if out.server_message:
            logger.info(f"Sync - Server message: {out.server_message}")

        accepted_sync_statuses = [out.NO_CHANGES, out.NORMAL_SYNC]
        status_str = anki.sync.SyncOutput.ChangesRequired.Name(out.required)
        if out.required not in accepted_sync_statuses:
            if mode in ["download", "upload"]:
                col.close_for_full_sync()
                logger.debug("Collection closed for full sync")
                try:
                    col.full_upload_or_download(
                        auth=auth,
                        server_usn=out.server_media_usn,
                        upload=(mode == "upload"),
                    )  # TODO media enabled option
                finally:
                    logger.debug("Reopening collection")
                    col.reopen(after_full_sync=True)
            else:
                logger.info(f"Could not sync status {status_str}")
                raise Exception(f"could not sync status {status_str} - use fullSync")
        logger.info(f"Synced with status: {status_str}")

    @util.api()
    def sync(self):
        self._sync()

    @util.api()
    def fullSync(self, mode: str):  # noqa: N802
        if mode not in ["upload", "download"]:
            raise ValueError("mode must be 'upload' or 'download'")
        self._sync(mode=mode)

    # TODO check Media

    @util.api()
    def checkDatabase(self):  # noqa: N802
        problems, ok = self.collection().fix_integrity()
        if ok:
            logger.info("Database integrity check passed")
        else:
            logger.error("Database integrity check failed")
        for problem in problems.split("\n"):
            if problem.strip():
                (logger.info if ok else logger.error)(problem)
        return {"problems": problems, "ok": ok}

    _last_mod = 0

    def check_and_update_modified(self):
        """Check if the database has been modified since the last check."""
        try:
            new_mod = self.collection().mod
            modified = new_mod != self.last_mod
            self.last_mod = new_mod
            return modified
        except AttributeError:
            logger.debug("Checked col.mod but database is not open")
            return False  # Database not open for some reason (probably syncing) TODO?

    def close(self):
        """Clean up resources and close the Anki collection."""
        try:
            if hasattr(self, "mock_mw"):
                self.mock_mw.close()
                logger.info("Bridge resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def collection(self) -> anki.collection.Collection:
        return super().collection()
