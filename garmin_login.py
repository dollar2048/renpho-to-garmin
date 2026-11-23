"""One-time Garmin Connect login. Saves tokens to ~/.garminconnect so other scripts need no password.

Usage:
    .venv/bin/python garmin_login.py
"""

from garmin_client import TOKEN_STORE, connect

if __name__ == "__main__":
    api = connect(interactive=True)
    print(f"Logged in as {api.get_full_name()}. Tokens saved in {TOKEN_STORE}")
