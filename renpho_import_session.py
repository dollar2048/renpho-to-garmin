"""Save the Renpho phone app's own session in the macOS Keychain.

Renpho allows one active session per account. Reusing the phone's token means
the sync and the phone app do not log each other out. Copy the values from any
request the phone app sends to cloud.renpho.com (for example with Proxyman):
request headers "token" and "userId".

Usage (run in a terminal, it asks for input; the token is not shown):
    .venv/bin/python renpho_import_session.py
"""

import sys

from renpho import RenphoAPIError, RenphoClient, RenphoSessionError

from renpho_client import load_saved, save


def main() -> int:
    saved = load_saved() or {}
    token = input_hidden("Renpho token (header 'token', hidden): ")
    default_user = saved.get("user_id", "")
    user_id = input(f"Renpho userId (header 'userId') [{default_user}]: ").strip() or str(default_user)
    if not token or not user_id.isdigit():
        print("Need a token and a numeric userId. Nothing saved.", file=sys.stderr)
        return 1

    client = RenphoClient.from_session({"token": token, "user_id": user_id, "email": saved.get("email", "")})
    try:
        profiles = client.get_measurement_profiles()  # read-only check; does not rotate the token
    except (RenphoAPIError, RenphoSessionError) as error:
        print(f"Renpho rejected this session ({error}). Nothing saved.", file=sys.stderr)
        return 1

    ids = [profile["user_id"] for profile in profiles]
    profile_user_id = saved.get("profile_user_id")
    if profile_user_id not in ids:
        print("Measurement profiles:")
        for number, profile_id in enumerate(ids, 1):
            print(f"  {number}. {profile_id}{' (account owner)' if profile_id == user_id else ''}")
        profile_user_id = ids[int(input(f"Which profile goes to Garmin? [1-{len(ids)}]: ").strip()) - 1]

    save(token, user_id, profile_user_id, saved.get("email", ""), client.token_expires_at)
    print(f"Phone session saved in Keychain item 'renpho-to-garmin.renpho' (profile {profile_user_id}).")
    return 0


def input_hidden(prompt: str) -> str:
    import getpass
    return getpass.getpass(prompt).strip()


if __name__ == "__main__":
    sys.exit(main())
