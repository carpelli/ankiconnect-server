"""
Anki-specific mock implementations.
Simple mocks for the Anki environment needed by AnkiConnect.
"""

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
        pass

    def reset(self):
        pass

    def unloadProfileAndShowProfileManager(self):
        pass

    def isVisible(self):
        return True

    def close(self):
        if hasattr(self, 'col') and self.col:
            self.col.close()
