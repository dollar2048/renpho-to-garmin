"""One-time Renpho Cloud login and profile choice.

Saves the session token and the chosen measurement profile in the macOS Keychain
(item "renpho-to-garmin.renpho"). The password itself is never stored.

Usage (run in a terminal, it asks for input):
    .venv/bin/python renpho_login.py
"""

import getpass
from datetime import datetime

from renpho import RenphoClient

from renpho_client import save_session


def describe_profile(client: RenphoClient, user_id: str) -> str:
    rows = client.get_all_measurements(profile_user_id=user_id)
    if not rows:
        return "no measurements"
    newest = rows[0]  # sorted newest first
    stamp = int(newest.get("timeStamp") or 0)
    stamp = stamp // 1000 if stamp > 1e12 else stamp  # Renpho sends seconds or milliseconds
    when = datetime.fromtimestamp(stamp).strftime("%Y-%m-%d")
    return f"{len(rows)} measurements, last {when}: {newest.get('weight')} kg"


def main() -> None:
    email = input("Renpho email: ").strip()
    password = getpass.getpass("Renpho password (hidden): ")
    client = RenphoClient(email, password)
    client.login()
    print("Logged in.")

    profiles = client.get_measurement_profiles()
    print("\nMeasurement profiles:")
    for number, profile in enumerate(profiles, 1):
        owner = " (account owner)" if profile["is_account_owner"] else ""
        print(f"  {number}. {profile['user_id']}{owner}: {describe_profile(client, profile['user_id'])}")

    choice = input(f"\nWhich profile goes to Garmin? [1-{len(profiles)}]: ").strip()
    chosen = profiles[int(choice) - 1]["user_id"]
    save_session(client, chosen)
    print(f"Session and profile {chosen} saved in Keychain item 'renpho-to-garmin.renpho'")


if __name__ == "__main__":
    main()
