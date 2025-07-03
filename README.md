# AnkiConnect Server

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

## API modifications

### sync
Since AnkiConnect only supports a partial sync, and there is no Anki client to fall back on and perform a full sync, the `sync` action is modified to support the parameter **mode**. This parameter must be set to `"upload"` or `"download"`. Caution is advised when using `"upload"`, as it might upload conflicting or corrupting changes caused by API calls. The parameter is only respected when a full sync is required, i.e. when the sync status is either of the following: `FULL_SYNC`, `FULL_DOWNLOAD` (empty local collection), or `FULL_UPLOAD` (empty remote collection).

Example request (use to download the collection from the sync server):

```Bash
curl localhost:8765 -X POST -d '{"action": "fullSync", "version": 6, "params": {"mode": "download"}}'
```

Replace `localhost:8765` with the address of your AnkiConnect server.

### requestPermission
Currently, `requestPermission` always returns a positive response

## Todo

- Implement CORS in requests (currently all requests are accepted)
- Log errors
- Nicer log output
- Flag to create database
- Report media sync status
- Investigate better way to store user credentials
- Import ankiconnect/plugin as a package from local source(?)
- Add server test code
- Test sync? (probably not worth the effort)
- Decide on how to copy init data to avoid strain on AnkiWeb
- Automate download sync on new collection creation
