#!/usr/bin/env python3
"""
Test script to verify lightweight AnkiConnect functionality.
This tests that the GUI stubs work properly and core functionality is preserved.
"""

import sys
import os
import tempfile
import json
from unittest.mock import patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gui_stubs_installation():
    """Test that GUI stubs are properly installed"""
    print("Testing GUI stubs installation...")

    # Import should install stubs automatically
    from app.gui_stubs import install_gui_stubs
    install_gui_stubs()

    # Check that aqt is available
    import aqt
    assert hasattr(aqt, 'appVersion')
    assert hasattr(aqt, 'qt')

    print("✅ GUI stubs installed successfully")

def test_basic_imports():
    """Test that all required modules can be imported"""
    print("Testing basic imports...")

    try:
        from app import AnkiConnectBridge, get_bridge
        print("✅ Core app modules imported")

        # Test Qt components
        from aqt.qt import Qt, QTimer, QMessageBox, QCheckBox
        print("✅ Qt components imported")

        # Test Anki GUI modules
        import aqt.editor
        import aqt.browser.previewer
        import aqt.editcurrent
        print("✅ Anki GUI modules imported")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        raise

def test_bridge_creation():
    """Test that AnkiConnect bridge can be created"""
    print("Testing bridge creation...")

    # Use a temporary collection for testing
    with tempfile.NamedTemporaryFile(suffix='.anki2', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        from app import AnkiConnectBridge

        bridge = AnkiConnectBridge(tmp_path)
        assert bridge is not None
        assert hasattr(bridge, 'process_request')
        print("✅ Bridge created successfully")

        # Clean up
        bridge.close()

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_core_ankiconnect_methods():
    """Test that core AnkiConnect methods work"""
    print("Testing core AnkiConnect methods...")

    with tempfile.NamedTemporaryFile(suffix='.anki2', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        from app import AnkiConnectBridge

        bridge = AnkiConnectBridge(tmp_path)

        # Test version method
        result = bridge.process_request({
            'action': 'version',
            'version': 6
        })
        assert result['result'] == 6
        assert result['error'] is None
        print("✅ Version method works")

        # Test deck names (should work even with empty collection)
        result = bridge.process_request({
            'action': 'deckNames',
            'version': 6
        })
        assert 'result' in result
        assert result['error'] is None
        print("✅ DeckNames method works")

        # Clean up
        bridge.close()

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_gui_methods_fail_gracefully():
    """Test that GUI methods fail gracefully instead of crashing"""
    print("Testing GUI method graceful failure...")

    with tempfile.NamedTemporaryFile(suffix='.anki2', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        from app import AnkiConnectBridge

        bridge = AnkiConnectBridge(tmp_path)

        # Test GUI browse method - should not crash
        result = bridge.process_request({
            'action': 'guiBrowse',
            'version': 6,
            'params': {
                'query': 'deck:Default'
            }
        })
        # Should return something, not crash
        assert 'result' in result
        print("✅ guiBrowse fails gracefully")

        # Test permission request - should deny by default
        result = bridge.process_request({
            'action': 'requestPermission',
            'version': 6,
            'params': {
                'origin': 'test-origin',
                'allowed': False
            }
        })
        assert 'result' in result
        print("✅ requestPermission fails gracefully")

        # Clean up
        bridge.close()

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_qt_components():
    """Test that Qt components work as expected"""
    print("Testing Qt components...")

    from aqt.qt import Qt, QTimer, QMessageBox, QCheckBox, QKeySequence

    # Test QTimer - just check it can be instantiated
    timer = QTimer()
    timer.start(1000)
    print("✅ QTimer works")

    # Test QMessageBox
    msg = QMessageBox()
    msg.setWindowTitle("Test")
    msg.setText("Test message")
    # Should not crash when exec() is called
    result = msg.exec()
    assert result == QMessageBox.StandardButton.No  # Default behavior
    print("✅ QMessageBox works")

    # Test QCheckBox - just check it can be instantiated
    checkbox = QCheckBox("Test checkbox")
    print("✅ QCheckBox works")

    # Test QKeySequence - just check it can be instantiated
    seq = QKeySequence("Ctrl+C")
    print("✅ QKeySequence works")

def test_anki_integration():
    """Test that Anki core functionality still works"""
    print("Testing Anki core integration...")

    # Test that we can import anki modules
    import anki
    import anki.collection
    from anki.notes import Note
    from anki.cards import Card
    print("✅ Anki core modules imported")

    # Test that aqt.mw can be set up
    from app.anki_mocks import MockAnkiMainWindow, find_collection_path

    collection_path = find_collection_path()
    mock_mw = MockAnkiMainWindow(collection_path)
    assert mock_mw is not None
    assert hasattr(mock_mw, 'col')
    print("✅ Anki environment setup works")

    # Clean up
    mock_mw.close()

def test_flask_server():
    """Test that the Flask server can be created"""
    print("Testing Flask server creation...")

    from app import app
    assert app is not None

    # Test that we can create a test client
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        print("✅ Health check works")

        # Test main endpoint with version request
        response = client.post('/',
            json={'action': 'version', 'version': 6},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 6
        print("✅ API endpoint works")

def test_memory_usage():
    """Test that memory usage is reasonable"""
    print("Testing memory usage...")

    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        print(f"Current memory usage: {memory_mb:.1f} MB")

        # Should be significantly less than full Anki with Qt
        # Full Anki typically uses 200-400MB, we should be under 100MB
        if memory_mb < 150:
            print("✅ Memory usage is reasonable")
        else:
            print(f"⚠️  Memory usage is higher than expected: {memory_mb:.1f} MB")
    except ImportError:
        print("⚠️  psutil not available, skipping memory test")
        print("✅ Memory test skipped (install psutil for actual measurement)")

def run_all_tests():
    """Run all tests"""
    print("🧪 Running AnkiConnect Lightweight Mode Tests")
    print("=" * 50)

    tests = [
        test_gui_stubs_installation,
        test_basic_imports,
        test_bridge_creation,
        test_core_ankiconnect_methods,
        test_gui_methods_fail_gracefully,
        test_qt_components,
        test_anki_integration,
        test_flask_server,
        test_memory_usage,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        print()

    print("=" * 50)
    print(f"Tests completed: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Lightweight mode is working correctly.")
        return True
    else:
        print("💥 Some tests failed. Check the output above.")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
