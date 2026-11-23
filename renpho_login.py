"""One-time Renpho Cloud login and profile choice.

Saves the session token to ~/.renpho/session.json and the chosen measurement
profile to ~/.renpho/config.json. The password itself is never stored.

Usage (run in a terminal, it asks for input):
    .venv/bin/python renpho_login.py
"""

import getpass
from datetime import datetime

from renpho import RenphoClient

from renpho_client import RENPHO_DIR, SESSION_FILE, save_profile_user_id


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
    RENPHO_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    client.save_session(SESSION_FILE)
    print(f"Logged in. Session saved in {SESSION_FILE}")

    profiles = client.get_measurement_profiles()
    print("\nMeasurement profiles:")
    for number, profile in enumerate(profiles, 1):
        owner = " (account owner)" if profile["is_account_owner"] else ""
        print(f"  {number}. {profile['user_id']}{owner}: {describe_profile(client, profile['user_id'])}")

    choice = input(f"\nWhich profile goes to Garmin? [1-{len(profiles)}]: ").strip()
    chosen = profiles[int(choice) - 1]["user_id"]
    save_profile_user_id(chosen)
    print(f"Saved profile {chosen}")


if __name__ == "__main__":
    main()
