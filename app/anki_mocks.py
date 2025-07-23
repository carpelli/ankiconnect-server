"""
Anki-specific mock implementations.
Simple mocks for the Anki environment needed by AnkiConnect.
"""

from anki.collection import Collection

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

    def getConfig(self, name):  # noqa: N802
        return get_ankiconnect_config()

    def writeConfig(self, addon_name, config):  # noqa: N802
        pass


class MockAnkiMainWindow:
    """Mock Anki main window"""

    def __init__(self, col: Collection):
        self.col = col
        self.addonManager = MockAddonManager()
        self.pm = MockProfileManager()
        self.progress = MockProgress()

    def requireReset(self, reason=None, context=None):  # noqa: N802
        pass

    def reset(self):
        pass

    def unloadProfileAndShowProfileManager(self):  # noqa: N802
        pass

    def isVisible(self):  # noqa: N802
        return True
