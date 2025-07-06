# AnkiConnect Server Test Suite

This directory contains tests for the AnkiConnect server implementation, extending beyond the original AnkiConnect plugin functionality.

## Test Structure

### Symlinked Tests (`tests/ankiconnect/`)
The following test files are symlinked from `libs/ankiconnect/tests/` and test the core AnkiConnect plugin functionality:
- `test_cards.py` - Card operations (suspend, unsuspend, etc.)
- `test_decks.py` - Deck management 
- `test_media.py` - Media file operations
- `test_misc.py` - Miscellaneous operations (version, profiles, export/import)
- `test_models.py` - Note type/model operations
- `test_notes.py` - Note CRUD operations and tagging
- `test_stats.py` - Statistics and review data

### Server-Specific Tests (`tests/`)
The following test files are unique to our server implementation and test functionality not covered by the original AnkiConnect plugin:

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

#### `test_config.py`
Tests configuration functionality and environment variable handling:
- **Environment Configuration**: Tests loading config from environment variables
- **AnkiConnect Config Generation**: Tests the config object structure and values
- **Configuration Validation**: Tests type conversion and error handling
- **Default Values**: Tests proper fallback to default configuration

#### `test_mocks.py`
Tests mock and GUI stub functionality that enables headless operation:
- **MinimalMock**: Tests the base mock class behavior and attributes
- **MockQt**: Tests Qt component mocking for GUI-less operation
- **MockQMessageBox**: Tests message box mocking for dialogs
- **MockGuiHooks**: Tests GUI hook system mocking
- **MockAqt**: Tests complete aqt module mocking
- **AnkiMocks**: Tests Anki main window, profile manager, and progress mocking
- **Integration**: Tests that all mocks work together properly

#### `test_cli.py`
Tests command line interface and server startup functionality:
- **Argument Parsing**: Tests command line argument processing
- **Server Startup**: Tests the run_server function and initialization
- **Error Handling**: Tests startup error scenarios and cleanup
- **Configuration Logging**: Tests API key and sync endpoint logging
- **Main Execution**: Tests the script's main execution logic

## Test Coverage

The expanded test suite provides comprehensive coverage of:

1. **Server Infrastructure**: HTTP handling, collection locking, auto-sync timers, lifecycle management
2. **Sync Functionality**: Authentication, sync operations, full sync, database integrity, error handling
3. **Bridge Integration**: Wrapper functionality, request routing, resource management
4. **Configuration Management**: Environment variables, config generation, validation, defaults
5. **Mock System**: GUI stubs, headless operation, Qt component mocking, Anki environment simulation
6. **Command Line Interface**: Argument parsing, server startup, error scenarios, logging
7. **Error Handling**: Graceful handling of failures across all components
8. **Logging**: Proper logging for debugging, monitoring, and operational visibility

## Functionality Coverage

### Previously Untested (Now Covered):
- Configuration loading and environment variable handling
- GUI stub installation and mock system behavior
- Server startup process and command line argument parsing
- Collection path handling and validation
- Mock Anki environment setup (profiles, progress, add-on manager)
- Server lifecycle management (startup, shutdown, cleanup)
- API key authentication configuration
- Sync endpoint configuration and logging

### Well Covered by Symlinked Tests:
- Core AnkiConnect API functionality (cards, decks, notes, models, etc.)
- Basic request/response handling
- Data validation and error responses

## Running Tests

Tests are designed to work with the existing conftest.py setup and use the same fixtures as the original AnkiConnect tests for consistency.

```bash
# Run all tests (both symlinked AnkiConnect tests and server-specific tests)
pytest tests/

# Run only the original AnkiConnect plugin tests
pytest tests/ankiconnect/

# Run only server-specific tests  
pytest tests/test_*.py

# Run specific test categories
pytest tests/test_server.py      # Server infrastructure and auto-sync
pytest tests/test_sync.py        # Sync functionality
pytest tests/test_bridge.py      # Bridge integration
pytest tests/test_config.py      # Configuration management
pytest tests/test_mocks.py       # Mock system and GUI stubs
pytest tests/test_cli.py         # Command line interface and startup
```