# AnkiConnect Server Test Suite

This directory contains tests for the AnkiConnect server implementation, extending beyond the original AnkiConnect plugin functionality.

## Test Structure

### Symlinked Tests
The following test files are symlinked from `libs/ankiconnect/tests/` and test the core AnkiConnect plugin functionality:
- `test_cards.py` - Card operations (suspend, unsuspend, etc.)
- `test_decks.py` - Deck management 
- `test_media.py` - Media file operations
- `test_misc.py` - Miscellaneous operations (version, profiles, export/import)
- `test_models.py` - Note type/model operations
- `test_notes.py` - Note CRUD operations and tagging
- `test_stats.py` - Statistics and review data

### Server-Specific Tests
The following test files are unique to our server implementation:

#### `test_server.py`
Tests server-specific functionality that extends beyond the basic AnkiConnect plugin:
- **Collection Locking**: Ensures thread-safe access to the Anki collection
- **Auto-Sync Timers**: Tests automatic sync scheduling after modifications and periodic sync
- **Sync Function**: Tests the sync wrapper with error handling
- **Server Lifecycle**: Tests proper cleanup of timers and resources
- **Request Permission Bypass**: Tests our specific permission handling
- **Collection Modification Tracking**: Tests detection of collection changes
- **Configuration Constants**: Validates sync timing constants

#### `test_sync.py`
Tests sync functionality using Anki's built-in sync server capabilities:
- **Sync Authentication**: Tests creation and validation of sync credentials
- **Basic Sync**: Tests normal sync operations with no changes and regular sync
- **Full Sync**: Tests upload and download full sync operations
- **Database Integrity**: Tests the checkDatabase functionality
- **Sync Error Handling**: Tests handling of network errors and sync failures
- **Sync Logging**: Tests proper logging of sync status and errors

#### `test_bridge.py`
Tests the AnkiConnectBridge class that wraps the original plugin:
- **Bridge Initialization**: Tests proper setup of collection paths and mock environment
- **Request Handling**: Tests request routing and permission bypassing
- **Sync Authentication**: Tests sync credential management
- **Bridge Cleanup**: Tests proper resource cleanup and error handling
- **Integration**: Tests that basic AnkiConnect functionality works through the bridge
- **Path Handling**: Tests handling of relative and absolute collection paths
- **Logging**: Tests proper logging during initialization and cleanup

## Test Coverage

The expanded test suite provides comprehensive coverage of:

1. **Server Infrastructure**: HTTP handling, collection locking, auto-sync timers
2. **Sync Functionality**: Authentication, sync operations, error handling
3. **Bridge Integration**: Wrapper functionality and resource management
4. **Error Handling**: Graceful handling of failures across all components
5. **Logging**: Proper logging for debugging and monitoring

## Running Tests

Tests are designed to work with the existing conftest.py setup and use the same fixtures as the original AnkiConnect tests for consistency.

```bash
# Run all tests
pytest tests/ankiconnect/

# Run specific test categories  
pytest tests/ankiconnect/test_server.py
pytest tests/ankiconnect/test_sync.py
pytest tests/ankiconnect/test_bridge.py
```