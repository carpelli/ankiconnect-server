"""
Anki-specific mock implementations.
Simple mocks for the Anki environment needed by AnkiConnect.
"""

import os
import sys
import anki
import anki.sync
from .config import get_ankiconnect_config

class MockProfileManager:
    """Mock profile manager"""

    def __init__(self):
        self.name = "test_user"

    def profiles(self):
        """Return list of available profiles"""
        return ["test_user"]

    def __getattr__(self, name):
        return None


class MockProgress:
    """Mock progress dialog"""

    def update(self, label=None, value=None, process=True):
        pass

    def finish(self):
        pass

    def start(self, max=0, min=0, immediate=False):
        pass


class MockAddonManager:
    """Mock addon manager"""

    def getConfig(self, name):
        return get_ankiconnect_config()

    def writeConfig(self, addon_name, config):
        pass


class MockAnkiMainWindow:
    """Mock Anki main window"""

    def __init__(self, collection_path: str):
        from anki.collection import Collection
        self.col = Collection(collection_path)
        self.addonManager = MockAddonManager()
        self.pm = MockProfileManager()
        self.progress = MockProgress()

    def requireReset(self, reason=None, context=None):
        """Mock requireReset method - does nothing in lightweight mode"""
        pass

    def reset(self):
        """Mock reset method - does nothing in lightweight mode"""
        pass

    def unloadProfileAndShowProfileManager(self):
        """Mock unload profile method"""
        pass

    def isVisible(self):
        """Mock isVisible method"""
        return True

    def close(self):
        if hasattr(self, 'col') and self.col:
            self.col.close()


def find_collection_path() -> str:
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

    # If User 1 doesn't exist, look for any profile
    if os.path.exists(base_path):
        for profile_dir in os.listdir(base_path):
            profile_path = os.path.join(base_path, profile_dir)
            if os.path.isdir(profile_path):
                collection_path = os.path.join(profile_path, "collection.anki2")
                if os.path.exists(collection_path):
                    return collection_path

    # Return the expected path anyway
    return user1_path
