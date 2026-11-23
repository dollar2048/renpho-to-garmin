"""Store session tokens in the macOS login Keychain (via the `keyring` library).

`keyring` talks to the Security framework directly, so secrets never appear on a
command line and have no length limit. Items are visible in Keychain Access as
"renpho-to-garmin.<name>". After a Python upgrade macOS may ask once to allow
access: choose "Always Allow".
"""

import keyring
from keyring.errors import PasswordDeleteError

PREFIX = "renpho-to-garmin."
ACCOUNT = "default"


def read(name: str) -> str | None:
    return keyring.get_password(PREFIX + name, ACCOUNT)


def write(name: str, value: str) -> None:
    keyring.set_password(PREFIX + name, ACCOUNT, value)
    if read(name) != value:  # never include the value in errors
        raise RuntimeError(f"Keychain write failed for {PREFIX + name}")


def delete(name: str) -> bool:
    try:
        keyring.delete_password(PREFIX + name, ACCOUNT)
        return True
    except PasswordDeleteError:
        return False
