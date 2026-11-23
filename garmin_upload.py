"""Upload a body-composition .fit file (made by renpho_to_fit.py) to Garmin Connect.

Usage:
    .venv/bin/python garmin_upload.py renpho_weight.fit
"""

import argparse
import json
import sys
from pathlib import Path

from garmin_client import connect


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fit_file", type=Path)
    args = parser.parse_args()

    if args.fit_file.suffix.lower() != ".fit" or not args.fit_file.is_file():
        sys.exit(f"Not a .fit file: {args.fit_file}")

    api = connect()
    body = api.upload_activity(str(args.fit_file))  # parsed JSON; HTTP errors raise
    print(f"Uploaded {args.fit_file}")
    if body:
        print(json.dumps(body, indent=2, ensure_ascii=False)[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
