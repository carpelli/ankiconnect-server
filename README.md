# Lightweight AnkiConnect Server

A lightweight wrapper for the AnkiConnect plugin that runs without requiring Anki desktop or the full PyQt GUI stack.

The server passes all requests to the original AnkiConnect plugin using minimal GUI stubs. Apps depending on the API work as-is, and changes are easily incorporated. GUI requests gracefully degrade to non-GUI alternatives or return sensible defaults instead of crashing.

## Features

- **Massive size reduction**: ~50MB instead of ~650MB (92% smaller)
- **Faster startup**: No GUI initialization overhead
- **Same API**: Drop-in replacement for existing AnkiConnect clients
- **Graceful degradation**: GUI methods fall back to functional alternatives
- **Container-friendly**: Perfect for Docker deployments

## Quick Start

```bash
poetry install
python -m app.main
```

The server runs on `http://localhost:8765` by default, just like regular AnkiConnect.

## What Works

✅ All core AnkiConnect functionality (deck/note/card operations)
✅ Search and filtering
✅ Import/export (programmatic)
⚠️ GUI methods return results but don't open windows
❌ Interactive permission dialogs

## Todo

- Implement CORS in requests (currently all requests are accepted)
- Log errors
- Non-existent databases are silently created?
- Report media sync status
- Investigate better way to store user credentials
