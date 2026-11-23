"""Shared Garmin Connect session: saved tokens first, interactive login only when asked."""

import getpass
import os
import sys
from pathlib import Path

from garminconnect import Garmin, GarminConnectAuthenticationError

TOKEN_STORE = Path(os.getenv("GARMINTOKENS", "~/.garminconnect")).expanduser()


def connect(interactive: bool = False) -> Garmin:
    """Return a logged-in client.

    Non-interactive: use saved tokens only, exit with a hint when they are missing or rejected.
    Interactive: ask email, password (hidden) and MFA code in the terminal, then save tokens.
    """
    if TOKEN_STORE.exists():
        try:
            api = Garmin()
            api.login(str(TOKEN_STORE))
            return api
        except GarminConnectAuthenticationError as error:
            if not interactive:
                sys.exit(f"Saved Garmin tokens do not work ({error}). Run: .venv/bin/python garmin_login.py")

    if not interactive:
        sys.exit("No saved Garmin tokens. Run first: .venv/bin/python garmin_login.py")

    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password (hidden): ")
    api = Garmin(email, password, prompt_mfa=lambda: input("MFA code: ").strip())
    TOKEN_STORE.mkdir(mode=0o700, parents=True, exist_ok=True)
    api.login(str(TOKEN_STORE))
    return api
