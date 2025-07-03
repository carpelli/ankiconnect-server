import os
import contextlib
import io
import argparse
import tempfile
from getpass import getpass
from pathlib import Path

from anki.errors import SyncError
import dotenv
from anki.collection import Collection

parser = argparse.ArgumentParser(description="generate an authorization token for an Anki sync server")
parser.add_argument('user', help='username (email)', nargs="?")
parser.add_argument('-e', '--endpoint', help='sync server address, defaults to .env file entry or AnkiWeb')
args = parser.parse_args()

dotenv.load_dotenv()
if not (endpoint := args.endpoint or os.getenv('SYNC_ENDPOINT')):
    print("no endpoint specified or found in .env, using AnkiWeb")
else:
    print(f"endpoint: {endpoint}")

if not (user := args.user or os.getenv('SYNC_USER')):
    user = input("user: ")
else:
    print(f"user: {user}")

password = getpass("password: ")

temp_col = tempfile.mkdtemp() / Path('temp.anki2')
col = Collection(str(temp_col))
try:
    with contextlib.redirect_stdout(io.StringIO()):
        hkey = col.sync_login(user, password, endpoint).hkey
except SyncError as e:
    print(e)
    exit(1)

print(f'key: {hkey}')

save = input(f"save to .env file? (y/n): ").lower().startswith('y')
if save:
    dotenv.set_key(dotenv.find_dotenv(), 'SYNC_KEY', hkey)
    print("saved! goodbye")
