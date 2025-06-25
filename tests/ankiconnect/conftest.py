"""
AnkiConnect Test Conftest - Lightweight Server Compatibility

This file provides all the fixtures, utilities, and mocks needed to run
original AnkiConnect tests with our lightweight server. It's designed to
replace the original conftest.py temporarily during test runs.

Key features:
- Drop-in replacement for original AnkiConnect conftest.py
- Provides same interface and fixtures as original
- Uses AnkiConnectBridge instead of full Anki GUI
- Mocks GUI components for headless testing
- Maintains compatibility with all original test expectations
"""

import os
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import pytest

# Add project root to Python path for imports
# Handle both cases: running from project root or from ankiconnect/tests directory
current_file = Path(__file__).resolve()
if 'libs/ankiconnect/tests' in str(current_file):
    # We're in libs/ankiconnect/tests, go up 4 levels to project root
    project_root = current_file.parent.parent.parent.parent
else:
    # We're in project root
    project_root = current_file.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import our bridge after path setup
from app import AnkiConnectBridge

# Global bridge instance for tests
_bridge = None
_temp_base_dir = None


def get_bridge():
    """Get or create the bridge instance"""
    global _bridge, _temp_base_dir
    if _bridge is None:
        # Create temporary collection for testing
        _temp_base_dir = tempfile.mkdtemp()
        collection_path = os.path.join(_temp_base_dir, "test_collection.anki2")
        _bridge = AnkiConnectBridge(collection_path=collection_path)
        # Add base attribute to match original session interface
        _bridge.base = _temp_base_dir
    return _bridge


class AnkiConnectWrapper:
    """Wrapper that provides the same interface as original AnkiConnect tests expect"""

    def __init__(self):
        self.bridge = get_bridge()
        self._ac = self.bridge.ankiconnect

    def __getattr__(self, name):
        """Delegate method calls to the bridge's AnkiConnect instance"""
        if hasattr(self._ac, name):
            return getattr(self._ac, name)
        raise AttributeError(f"AnkiConnect has no method '{name}'")

    def collection(self):
        """Return the collection for direct access"""
        return self._ac.collection()


# Mock classes for GUI functionality that AnkiConnect tests might expect
class MockTaskManager:
    """Mock task manager for background operations"""

    def run_in_background(self, task, on_done=None, kwargs=None):
        """Execute task synchronously (no background threading needed)"""
        import concurrent.futures
        future = concurrent.futures.Future()

        try:
            result = task(**kwargs if kwargs is not None else {})
            future.set_result(result)
        except BaseException as e:
            future.set_exception(e)

        if on_done is not None:
            on_done(future)


class MockProgressDialog:
    """Mock progress dialog for operations that show progress"""

    def __init__(self):
        self.value = 0
        self.max = 100
        self._label = ""

    def update(self, value=None, label=None):
        if value is not None:
            self.value = value
        if label is not None:
            self._label = label

    def finish(self):
        pass

    def setCancelable(self, cancelable):
        pass


class MockProfileManager:
    """Mock profile manager"""

    def __init__(self):
        self.name = "test_profile"

    def profiles(self):
        return ["test_profile"]

    def setMeta(self, key, value):
        pass


class MockMainWindow:
    """Mock main window"""

    def __init__(self):
        self.pm = MockProfileManager()
        self.progress = MockProgressDialog()
        self.taskman = MockTaskManager()

    def checkpoint(self, name):
        pass

    def reset(self):
        pass

    def requireReset(self, modal=False):
        pass


# Mock aqt module structure to satisfy imports
class MockAqtOperationsNote:
    @staticmethod
    def add_note(*args, **kwargs):
        pass

    @staticmethod
    def update_note(*args, **kwargs):
        pass


class MockAqtOperations:
    note = MockAqtOperationsNote


class MockAqt:
    """Mock aqt module with necessary structure"""
    operations = MockAqtOperations

    def __init__(self):
        self.mw = MockMainWindow()


# Set up mock aqt module in sys.modules to satisfy imports
if 'aqt' not in sys.modules:
    mock_aqt = MockAqt()
    sys.modules['aqt'] = mock_aqt
    sys.modules['aqt.operations'] = MockAqtOperations
    sys.modules['aqt.operations.note'] = MockAqtOperationsNote

# Create global instances that AnkiConnect tests expect
ac = AnkiConnectWrapper()
anki_version = (2, 1, 70)  # Mock version matching original


# Utility functions from original conftest.py
def wait(seconds):
    """Wait function - simplified without Qt"""
    time.sleep(seconds)


def wait_until(booleanish_function, at_most_seconds=30):
    """Wait until condition is met"""
    deadline = time.time() + at_most_seconds

    while time.time() < deadline:
        if booleanish_function():
            return
        time.sleep(0.01)

    raise Exception(f"Function {booleanish_function} never returned "
                   f"a positive value in {at_most_seconds} seconds")


def delete_model(model_name):
    """Delete a model by name"""
    try:
        model = ac.collection().models.by_name(model_name)
        if model:
            ac.collection().models.remove(model["id"])
    except:
        pass  # Model might not exist


def close_all_dialogs_and_wait_for_them_to_run_closing_callbacks():
    """Mock function - no dialogs in lightweight mode"""
    pass


def get_dialog_instance(name):
    """Mock function - no dialogs in lightweight mode"""
    return None


@contextmanager
def current_decks_and_models_etc_preserved():
    """Preserve deck and model state during tests"""
    try:
        deck_names_before = set(ac.deckNames())
        model_names_before = set(ac.modelNames())
    except:
        deck_names_before = set()
        model_names_before = set()

    try:
        yield
    finally:
        try:
            deck_names_after = set(ac.deckNames())
            model_names_after = set(ac.modelNames())

            deck_names_to_delete = deck_names_after - deck_names_before
            model_names_to_delete = model_names_after - model_names_before

            if deck_names_to_delete:
                ac.deleteDecks(decks=list(deck_names_to_delete), cardsToo=True)

            for model_name in model_names_to_delete:
                delete_model(model_name)

            # Try to trigger deck browser refresh (matches original)
            try:
                ac.guiDeckBrowser()
            except:
                pass
        except:
            pass  # Best effort cleanup


@dataclass
class Setup:
    """Data class matching original conftest.py Setup"""
    deck_id: int
    note1_id: int
    note2_id: int
    note1_card_ids: "list[int]"
    note2_card_ids: "list[int]"
    card_ids: "list[int]"


def set_up_test_deck_and_test_model_and_two_notes():
    """Set up test data exactly like original conftest.py"""
    ac.createModel(
        modelName="test_model",
        inOrderFields=["field1", "field2"],
        cardTemplates=[
            {"Front": "{{field1}}", "Back": "{{field2}}"},
            {"Front": "{{field2}}", "Back": "{{field1}}"}
        ],
        css="* {}",
    )

    deck_id = ac.createDeck("test_deck")

    note1_id = ac.addNote(dict(
        deckName="test_deck",
        modelName="test_model",
        fields={"field1": "note1 field1", "field2": "note1 field2"},
        tags={"tag1"},
    ))

    note2_id = ac.addNote(dict(
        deckName="test_deck",
        modelName="test_model",
        fields={"field1": "note2 field1", "field2": "note2 field2"},
        tags={"tag2"},
    ))

    note1_card_ids = ac.findCards(query=f"nid:{note1_id}")
    note2_card_ids = ac.findCards(query=f"nid:{note2_id}")
    card_ids = ac.findCards(query="deck:test_deck")

    return Setup(
        deck_id=deck_id,
        note1_id=note1_id,
        note2_id=note2_id,
        note1_card_ids=note1_card_ids,
        note2_card_ids=note2_card_ids,
        card_ids=card_ids,
    )


# Context managers that may be used by original tests
@contextmanager
def anki_connect_config_loaded(session, web_bind_port):
    """Mock config loading context manager"""
    yield


@contextmanager
def waitress_patched_to_prevent_it_from_dying():
    """Mock waitress patching - not needed in lightweight mode"""
    yield


@contextmanager
def anki_patched_to_prevent_backups():
    """Mock backup prevention - not needed in lightweight mode"""
    yield


@contextmanager
def empty_anki_session_started():
    """Mock empty session context manager"""
    yield get_bridge()


@contextmanager
def profile_created_and_loaded(session):
    """Mock profile loading context manager"""
    yield session


# Pytest fixtures matching original conftest.py interface
@pytest.fixture(scope="session")
def session_scope_empty_session():
    """Session-scoped empty session fixture"""
    yield get_bridge()


@pytest.fixture(scope="session")
def session_scope_session_with_profile_loaded(session_scope_empty_session):
    """Session-scoped session with profile loaded"""
    yield session_scope_empty_session


@pytest.fixture
def session_with_profile_loaded(session_scope_empty_session):
    """Session with profile loaded - matches original interface"""
    with current_decks_and_models_etc_preserved():
        yield session_scope_empty_session


@pytest.fixture
def setup(session_with_profile_loaded):
    """Test setup fixture that creates test deck and notes"""
    # Register Edit dialog if it exists (from original)
    try:
        from plugin.edit import Edit
        Edit.register_with_anki()
    except:
        pass

    yield set_up_test_deck_and_test_model_and_two_notes()
    close_all_dialogs_and_wait_for_them_to_run_closing_callbacks()


@pytest.fixture(autouse=True)
def run_background_tasks_on_main_thread(monkeypatch):
    """Mock background task execution - auto-use fixture"""
    # This fixture is automatically applied to all tests
    pass


# Pytest configuration hooks
def pytest_report_header(config):
    """Report test configuration"""
    return "AnkiConnect lightweight server mode; using temporary collection"


# Additional globals that might be referenced by original tests
# These are available at module level for direct import by test files
# (This matches the interface that original AnkiConnect tests expect)
