# AnkiConnect Server

A lightweight server wrapper for the [AnkiConnect plugin](https://git.sr.ht/~foosoft/anki-connect/) that runs without requiring Anki desktop or the full PyQt GUI stack.

The server passes all requests to the original AnkiConnect plugin using minimal GUI stubs. AnkiConnect clients should work as-is, and updates to the original plugin are easily incorporated. GUI requests are not tested, but should return appropriate fallback responses.

- **Small and fast**: Without any GUI, the application has a small footprint, starts up quickly, and uses comparitively few resources
- **API compatibility**: Drop-in replacement for existing AnkiConnect clients. All deck, note, card, import/export, and search and filter operations work as expected.
- **Easy deployment**: Just run the container

> [!NOTE]
> This is not an Anki sync server, but a client that functions as a server for the AnkiConnect API. To sync your data with other Anki clients, you'll need to connect with a server (instructions below).

### Why this exists

I wanted to use the KOReader Anki plugin and immediately see the new cards on my phone without opening my computer first. I experimented with a headless Anki container, but decided that this option was more dependable and easier on my server.

## Usage

### Quick start

After installing the dependencies:

```bash
python -m app.server
```

The server runs on `http://localhost:8765` by default, and can be configured using the environment variables in `.env.example`. If you start the server with an empty collection, you'll need to use the `fullSync` action detailed below in order to load your data.

#### Docker

For easy deployment, use the Dockerfile. Note that you still need to obtain a sync key.

### Sync authentication

In order to sync the collection with the sync server, you'll need to provide an authentication key. This key can be requested by running

```bash
python -m app.keygen
```

Follow the prompts to obtain your key.

## API Extensions

#### fullSync
Since AnkiConnect only supports partial syncs and there's no Anki client to handle full syncs, a `fullSync` action is provided with a **mode** parameter. Set this to `"upload"` or `"download"`. Use `"upload"` with caution as it may upload conflicting changes from API operations. This action only performs a full sync if it is required (sync status: `FULL_SYNC`, `FULL_DOWNLOAD`, or `FULL_UPLOAD`).

Example request to download the collection from the sync server:

```bash
curl localhost:8765 -X POST -d '{"action": "fullSync", "version": 6, "params": {"mode": "download"}}'
```

#### checkDatabase
Performs the equivalent of Anki's "Check Database" function. Returns a boolean `ok` indicating success and `problems` containing any issues found.

#### requestPermission
Currently returns a positive response for all permission requests.

## Todo

- Implement CORS in requests (currently all requests are accepted)
- Check collection from time to time
- Log errors
- Nicer log output
- Flag to create database
- Report media sync status?
- Import ankiconnect/plugin as a package from local source(?)
- Add server test code
- Test sync? (probably not worth the effort)
- Decide on how to copy init data to avoid strain on AnkiWeb
- Automate download sync on new collection creation
- Use anki collection dir instead of file
