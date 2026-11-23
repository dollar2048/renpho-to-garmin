"""Shared Renpho Cloud session (via renpho-py): saved session file, no password at sync time."""

import json
import sys
from pathlib import Path

from renpho import RenphoAPIError, RenphoClient, RenphoSessionError

RENPHO_DIR = Path("~/.renpho").expanduser()
SESSION_FILE = RENPHO_DIR / "session.json"
CONFIG_FILE = RENPHO_DIR / "config.json"  # {"profile_user_id": "..."}


def connect() -> RenphoClient:
    """Client from the saved session. Never logs in with a password."""
    if not SESSION_FILE.exists():
        sys.exit("No saved Renpho session. Run first: .venv/bin/python renpho_login.py")
    client = RenphoClient.from_session_file(SESSION_FILE)
    try:
        client.refresh_session()  # adopts a replacement token if Renpho issues one; saves it
    except (RenphoAPIError, RenphoSessionError) as error:
        sys.exit(f"Renpho session does not work ({error}). Run: .venv/bin/python renpho_login.py")
    return client


def load_profile_user_id() -> str:
    try:
        return str(json.loads(CONFIG_FILE.read_text())["profile_user_id"])
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        sys.exit("No Renpho profile chosen. Run: .venv/bin/python renpho_login.py")


def save_profile_user_id(user_id: str) -> None:
    RENPHO_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"profile_user_id": str(user_id)}, indent=2) + "\n")
    CONFIG_FILE.chmod(0o600)
