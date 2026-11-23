"""Shared Garmin Connect session: tokens from the macOS Keychain, interactive login only when asked."""

import atexit
import getpass
import sys

from garminconnect import Garmin, GarminConnectAuthenticationError

import keychain_store

KEYCHAIN_NAME = "garmin"  # Keychain item "renpho-to-garmin.garmin"


def _save_tokens(api: Garmin) -> None:
    tokens = api.client.dumps()
    if tokens != keychain_store.read(KEYCHAIN_NAME):
        keychain_store.write(KEYCHAIN_NAME, tokens)


def connect(interactive: bool = False) -> Garmin:
    """Return a logged-in client.

    Non-interactive: use saved tokens only, exit with a hint when they are missing or rejected.
    Interactive: always ask email, password (hidden) and MFA code, then replace the saved tokens.
    Refreshed tokens are written back to the Keychain when the process ends.
    """
    tokens = None if interactive else keychain_store.read(KEYCHAIN_NAME)
    if tokens:
        try:
            api = Garmin()
            api.login(tokens)  # the library accepts token JSON instead of a folder path
            atexit.register(_save_tokens, api)
            return api
        except GarminConnectAuthenticationError as error:
            sys.exit(f"Saved Garmin tokens do not work ({error}). Run: .venv/bin/python garmin_login.py")

    if not interactive:
        sys.exit("No saved Garmin tokens. Run first: .venv/bin/python garmin_login.py")

    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password (hidden): ")
    api = Garmin(email, password, prompt_mfa=lambda: input("MFA code: ").strip())
    api.login()
    _save_tokens(api)
    atexit.register(_save_tokens, api)
    return api
