"""
Adaptation of libs/ankiconnect/tests/conftest.py to run the same tests with our own AnkiConnectBridge
"""

import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.core import AnkiConnectBridge

# Add path so test files (which are symlinked) can import this conftest.py
sys.path.append("tests/ankiconnect")

# Create global instances that AnkiConnect tests expect
temp_dir = tempfile.mkdtemp()
ac = AnkiConnectBridge(base_dir=Path(temp_dir))
setattr(ac, "base", temp_dir)


# wait for n seconds, while events are being processed
def wait(seconds):
    time.sleep(seconds)


def delete_model(model_name):
    model = ac.collection().models.by_name(model_name)
    ac.collection().models.remove(model["id"])


@contextmanager
def current_decks_and_models_etc_preserved():
    """Preserve deck and model state during tests"""
    deck_names_before = set(ac.deckNames())
    model_names_before = set(ac.modelNames())

    try:
        yield
    finally:
        deck_names_after = set(ac.deckNames())
        model_names_after = set(ac.modelNames())

        # Clean up new decks and models
        ac.deleteDecks(decks=deck_names_after - deck_names_before, cardsToo=True)
        for model_name in model_names_after - model_names_before:
            delete_model(model_name)


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
            {"Front": "{{field2}}", "Back": "{{field1}}"},
        ],
        css="* {}",
    )

    deck_id = ac.createDeck("test_deck")

    note1_id = ac.addNote(
        dict(
            deckName="test_deck",
            modelName="test_model",
            fields={"field1": "note1 field1", "field2": "note1 field2"},
            tags={"tag1"},
        )
    )

    note2_id = ac.addNote(
        dict(
            deckName="test_deck",
            modelName="test_model",
            fields={"field1": "note2 field1", "field2": "note2 field2"},
            tags={"tag2"},
        )
    )

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
    yield


# Pytest fixtures matching original conftest.py interface
@pytest.fixture(scope="session")
def session_scope_empty_session():
    yield ac


@pytest.fixture(scope="session")
def session_scope_session_with_profile_loaded(session_scope_empty_session):
    yield session_scope_empty_session


@pytest.fixture
def session_with_profile_loaded(session_scope_empty_session):
    with current_decks_and_models_etc_preserved():
        yield session_scope_empty_session


@pytest.fixture
def setup(session_with_profile_loaded):
    yield set_up_test_deck_and_test_model_and_two_notes()


# Pytest configuration hooks
def pytest_sessionfinish(session, exitstatus):
    ac.close()
    shutil.rmtree(temp_dir)
