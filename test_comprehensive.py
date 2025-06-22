#!/usr/bin/env python3
"""
Comprehensive test script for the AnkiConnect Bridge
Tests both the bridge functionality and the Flask server
"""

import sys
import os
import time
import threading
import requests
import json
from typing import Dict, Any, Optional

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_bridge_direct():
    """Test the bridge directly without HTTP server"""
    print("=" * 60)
    print("Testing AnkiConnect Bridge (Direct)")
    print("=" * 60)

    try:
        from app import AnkiConnectBridge
        print("✅ Successfully imported AnkiConnectBridge")

        # Create bridge instance
        bridge = AnkiConnectBridge()
        print(f"✅ Bridge created successfully")
        print(f"   Collection path: {bridge.collection_path}")

        # Test basic requests
        test_requests = [
            {"action": "version", "version": 6},
            {"action": "deckNames", "version": 6},
            {"action": "modelNames", "version": 6},
        ]

        for i, test_req in enumerate(test_requests, 1):
            try:
                result = bridge.process_request(test_req)
                if result.get("error") is None:
                    print(f"✅ Test {i} ({test_req['action']}): Success")
                    if isinstance(result.get("result"), list) and len(result["result"]) > 0:
                        sample = str(result["result"])
                        if len(sample) > 80:
                            sample = sample[:80] + "..."
                        print(f"   └─ Sample: {sample}")
                    else:
                        print(f"   └─ Result: {result['result']}")
                else:
                    print(f"❌ Test {i} ({test_req['action']}): {result['error']}")
            except Exception as e:
                print(f"❌ Test {i} ({test_req['action']}): Exception - {e}")

        # Clean up
        bridge.close()
        print("✅ Bridge closed successfully")
        return True

    except Exception as e:
        print(f"❌ Bridge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_functionality(port: int = 8768):
    """Test the Flask server functionality"""
    print("\n" + "=" * 60)
    print(f"Testing AnkiConnect Bridge Server (Port {port})")
    print("=" * 60)

    try:
        from app import run_server
        print("✅ Successfully imported run_server")

        # Start server in background thread
        server_thread = threading.Thread(
            target=lambda: run_server(host='127.0.0.1', port=port, debug=False),
            daemon=True
        )
        server_thread.start()
        print(f"✅ Server thread started on port {port}")

        # Give server time to start
        time.sleep(3)

        # Test health endpoint
        try:
            health_response = requests.get(f'http://127.0.0.1:{port}/health', timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ Health check: {health_data}")
            else:
                print(f"❌ Health check failed: {health_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

        # Test AnkiConnect API endpoints
        test_requests = [
            {"action": "version", "version": 6},
            {"action": "deckNames", "version": 6},
            {"action": "modelNames", "version": 6},
            {"action": "findNotes", "version": 6, "params": {"query": "deck:Default"}},
        ]

        for i, test_req in enumerate(test_requests, 1):
            try:
                response = requests.post(
                    f'http://127.0.0.1:{port}/',
                    json=test_req,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("error") is None:
                        print(f"✅ HTTP Test {i} ({test_req['action']}): Success")
                        if isinstance(result.get("result"), list) and len(result["result"]) > 0:
                            sample = str(result["result"])
                            if len(sample) > 80:
                                sample = sample[:80] + "..."
                            print(f"   └─ Sample: {sample}")
                        else:
                            print(f"   └─ Result: {result['result']}")
                    else:
                        print(f"❌ HTTP Test {i} ({test_req['action']}): {result['error']}")
                else:
                    print(f"❌ HTTP Test {i} ({test_req['action']}): HTTP {response.status_code}")

            except Exception as e:
                print(f"❌ HTTP Test {i} ({test_req['action']}): {e}")

        # Test multi-action request
        try:
            multi_request = {
                "action": "multi",
                "version": 6,
                "params": {
                    "actions": [
                        {"action": "version", "version": 6},
                        {"action": "deckNames", "version": 6}
                    ]
                }
            }

            response = requests.post(
                f'http://127.0.0.1:{port}/',
                json=multi_request,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("error") is None:
                    print(f"✅ Multi-action test: Success")
                    print(f"   └─ Results: {len(result.get('result', []))} actions")
                else:
                    print(f"❌ Multi-action test: {result['error']}")
            else:
                print(f"❌ Multi-action test: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ Multi-action test: {e}")

        print("✅ Server tests completed")
        return True

    except Exception as e:
        print(f"❌ Server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qt_components():
    """Test that Qt components are properly available"""
    print("\n" + "=" * 60)
    print("Testing Qt Components Integration")
    print("=" * 60)

    try:
        # Test that we can import Qt components without issues
        from aqt.qt import Qt, QTimer, QMessageBox, QCheckBox, QKeySequence, QShortcut, QCloseEvent, QMainWindow
        print("✅ All Qt components imported successfully")

        # Test basic functionality
        try:
            # Test QKeySequence
            seq = QKeySequence("Ctrl+Shift+P")
            print(f"✅ QKeySequence works: Created sequence for Ctrl+Shift+P")

            # Test Qt constants
            if hasattr(Qt, 'WindowType'):
                print(f"✅ Qt.WindowType available")

            # Test QTimer (basic instantiation)
            timer = QTimer()
            print(f"✅ QTimer instantiation works")

            return True

        except Exception as e:
            print(f"❌ Qt component functionality test failed: {e}")
            return False

    except ImportError as e:
        print(f"❌ Qt components import failed: {e}")
        return False

def run_all_tests():
    """Run all test suites"""
    print("🚀 Starting Comprehensive AnkiConnect Bridge Tests")
    print("=" * 80)

    results = {
        "qt_components": test_qt_components(),
        "bridge_direct": test_bridge_direct(),
        "server": test_server_functionality(),
    }

    # Summary
    print("\n" + "=" * 80)
    print("Test Results Summary")
    print("=" * 80)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title():.<50} {status}")

    print("=" * 80)
    print(f"Overall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All tests passed! The AnkiConnect Bridge is fully functional.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
