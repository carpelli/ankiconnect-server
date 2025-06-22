"""
Anki-specific mock implementations.
Simple mocks for the Anki environment needed by AnkiConnect.
"""

import os
import sys
from .config import get_ankiconnect_config


class MockAnkiMainWindow:
    """Mock Anki main window"""

    def __init__(self, collection_path: str):
        from anki.collection import Collection
        self.col = Collection(collection_path)
        self.addonManager = MockAddonManager()

    def close(self):
        if hasattr(self, 'col') and self.col:
            self.col.close()


class MockAddonManager:
    """Mock addon manager"""

    def getConfig(self, name):
        return get_ankiconnect_config()

    def writeConfig(self, addon_name, config):
        pass


def find_collection_path():
    """Find the default Anki collection path"""
    # Check environment variable first
    env_path = os.getenv('ANKICONNECT_COLLECTION_PATH')
    if env_path and os.path.exists(env_path):
        return env_path

    # Auto-detect based on platform
    if sys.platform == "win32":
        base_path = os.path.expanduser("~/AppData/Roaming/Anki2")
    elif sys.platform == "darwin":
        base_path = os.path.expanduser("~/Library/Application Support/Anki2")
    else:
        base_path = os.path.expanduser("~/.local/share/Anki2")

    # Look for User 1 profile (default)
    user1_path = os.path.join(base_path, "User 1", "collection.anki2")
    if os.path.exists(user1_path):
        return user1_path

    # Return the expected path anyway
    return user1_path
