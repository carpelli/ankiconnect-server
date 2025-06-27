"""
AnkiConnect Test Conftest - Lightweight Server Compatibility

This file provides all the fixtures, utilities, and mocks needed to run
original AnkiConnect tests with our lightweight server. It's designed to
replace the original conftest.py temporarily during test runs.

Key features:
- Drop-in replacement for original AnkiConnect conftest.py
- Provides same interface and fixtures as original
- Uses AnkiConnectBridge instead of full Anki GUI
- Reuses existing mock implementations from app/
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

from app.gui_stubs import install_gui_stubs
install_gui_stubs()

from app.core import AnkiConnectBridge

# Add paths so test files can import plugin and conftest
sys.path.extend(['libs/ankiconnect', str(Path(__file__).parent)])


class AnkiConnectWrapper:
    """Wrapper that provides the same interface as original AnkiConnect tests expect"""

    def __init__(self):
        temp_dir = tempfile.mkdtemp()
        collection_path = os.path.join(temp_dir, "test_collection.anki2")
        self.bridge = AnkiConnectBridge(collection_path=collection_path)
        setattr(self.bridge, 'base', temp_dir)  # Match original session interface
        self._ac = self.bridge.ankiconnect

    def __getattr__(self, name):
        """Delegate method calls to the bridge's AnkiConnect instance"""
        if hasattr(self._ac, name):
            return getattr(self._ac, name)
        raise AttributeError(f"AnkiConnect has no method '{name}'")

    def collection(self):
        """Return the collection for direct access"""
        return self._ac.collection()

    def close(self):
        """Close the bridge and clean up resources"""
        if hasattr(self, 'bridge'):
            self.bridge.close()


# Create global instances that AnkiConnect tests expect
ac = AnkiConnectWrapper()


# Utility functions from original conftest.py
def wait(seconds):
    """Wait function - simplified without Qt"""
    time.sleep(seconds)


def delete_model(model_name):
    """Delete a model by name"""
    try:
        model = ac.collection().models.by_name(model_name)
        if model:
            ac.collection().models.remove(model["id"])
    except:
        pass  # Model might not exist


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

            # Clean up new decks and models
            for deck_name in deck_names_after - deck_names_before:
                ac.deleteDecks(decks=[deck_name], cardsToo=True)
            for model_name in model_names_after - model_names_before:
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


# Pytest fixtures matching original conftest.py interface
@pytest.fixture(scope="session")
def session_scope_empty_session():
    """Session-scoped empty session fixture"""
    yield ac.bridge


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
    except ImportError:
        pass

    yield set_up_test_deck_and_test_model_and_two_notes()


# Pytest configuration hooks
def pytest_sessionfinish(session, exitstatus):
    """Clean up resources when test session ends"""
    try:
        ac.close()
    except:
        pass  # Best effort cleanup
