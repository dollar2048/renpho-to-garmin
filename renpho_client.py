"""Shared Renpho Cloud session (via renpho-py) kept in the macOS Keychain; no password at sync time.

Renpho allows one active session per account: a new login on the phone revokes
ours and our login revokes the phone's. renpho_import_session.py stores the
phone's own session instead, so both keep working.

Keychain item "renpho-to-garmin.renpho" holds JSON:
    {"email", "user_id", "token", "expires_at", "profile_user_id"}
"""

import json
import sys
import time

from renpho import RenphoClient

import keychain_store

KEYCHAIN_NAME = "renpho"
RELOGIN_HINT = (
    "Copy the current token from the Renpho phone app and run: .venv/bin/python renpho_import_session.py"
)


def load_saved() -> dict | None:
    raw = keychain_store.read(KEYCHAIN_NAME)
    return json.loads(raw) if raw else None


def save(token: str, user_id: str, profile_user_id: str, email: str = "", expires_at: float | None = None) -> None:
    data = {
        "email": email,
        "user_id": str(user_id),
        "token": token,
        "expires_at": expires_at,
        "profile_user_id": str(profile_user_id),
    }
    keychain_store.write(KEYCHAIN_NAME, json.dumps(data))


def save_session(client: RenphoClient, profile_user_id: str) -> None:
    save(client.token, client.user_id, profile_user_id, client.email, client.token_expires_at)


def connect() -> RenphoClient:
    """Client from the saved session. Never logs in and never asks Renpho for a new token.

    No refresh_session(): with a session shared with the phone, a token rotation
    on our side would log the phone out.
    """
    data = load_saved()
    if not data:
        sys.exit(f"No saved Renpho session. {RELOGIN_HINT}")
    client = RenphoClient.from_session(data)
    expires_at = client.token_expires_at
    if expires_at is not None and expires_at < time.time():
        sys.exit(f"Renpho session expired. {RELOGIN_HINT}")
    return client


def load_profile_user_id() -> str:
    data = load_saved() or {}
    if not data.get("profile_user_id"):
        sys.exit("No Renpho profile chosen. Run: .venv/bin/python renpho_import_session.py")
    return str(data["profile_user_id"])
