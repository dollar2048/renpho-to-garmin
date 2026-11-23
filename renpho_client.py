"""Shared Renpho Cloud session (via renpho-py) kept in the macOS Keychain; no password at sync time.

Keychain item "renpho-to-garmin.renpho" holds JSON:
    {"email", "user_id", "token", "expires_at", "profile_user_id"}
"""

import json
import sys

from renpho import RenphoAPIError, RenphoClient, RenphoSessionError

import keychain_store

KEYCHAIN_NAME = "renpho"


def _load() -> dict:
    raw = keychain_store.read(KEYCHAIN_NAME)
    if not raw:
        sys.exit("No saved Renpho session. Run first: .venv/bin/python renpho_login.py")
    return json.loads(raw)


def save_session(client: RenphoClient, profile_user_id: str) -> None:
    data = {
        "email": client.email,
        "user_id": client.user_id,
        "token": client.token,
        "expires_at": client.token_expires_at,
        "profile_user_id": str(profile_user_id),
    }
    keychain_store.write(KEYCHAIN_NAME, json.dumps(data))


def connect() -> RenphoClient:
    """Client from the saved session. Never logs in with a password."""
    data = _load()
    client = RenphoClient.from_session(data)
    try:
        client.refresh_session()  # Renpho may issue a replacement token
    except (RenphoAPIError, RenphoSessionError) as error:
        sys.exit(f"Renpho session does not work ({error}). Run: .venv/bin/python renpho_login.py")
    if client.token != data["token"]:
        save_session(client, data["profile_user_id"])
    return client


def load_profile_user_id() -> str:
    data = _load()
    if not data.get("profile_user_id"):
        sys.exit("No Renpho profile chosen. Run: .venv/bin/python renpho_login.py")
    return str(data["profile_user_id"])
