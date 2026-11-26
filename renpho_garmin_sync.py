"""Sync new Renpho Cloud weigh-ins to Garmin Connect.

Takes all Renpho measurements of the saved profile (or only the last --days days),
skips every one whose exact time already exists in Garmin, uploads the rest as
one FIT file and checks that Garmin stored them. Comparing the full history by
default means a weigh-in missed by an earlier run is still picked up later.

Usage:
    .venv/bin/python renpho_garmin_sync.py --dry-run
    .venv/bin/python renpho_garmin_sync.py
    .venv/bin/python renpho_garmin_sync.py --days 30
"""

import argparse
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from garmin_client import connect as connect_garmin
from garmin_weighins import fetch_weigh_ins
from renpho import RenphoAPIError, RenphoSessionError

from renpho_client import RELOGIN_HINT, connect as connect_renpho, load_profile_user_id
from renpho_to_fit import Measurement, build_fit


def _float(value) -> float | None:
    return None if value in (None, "", 0, 0.0) else float(value)


def from_renpho(row: dict) -> Measurement | None:
    """Map one Renpho Cloud record to a Measurement; None for invalid rows."""
    weight = _float(row.get("weight"))
    stamp = int(row.get("timeStamp") or 0)
    if weight is None or stamp <= 0 or row.get("invalidFlag"):
        return None
    stamp = stamp // 1000 if stamp > 1e12 else stamp  # seconds or milliseconds
    muscle_percent = _float(row.get("muscle"))  # skeletal muscle %
    visfat = _float(row.get("visfat"))
    bodyage = _float(row.get("bodyage"))
    return Measurement(
        # timeStamp is UTC epoch; localCreatedAt is server time, not the user's, so it is ignored.
        taken_at=datetime.fromtimestamp(stamp, timezone.utc),
        weight=weight,
        bmi=_float(row.get("bmi")),
        percent_fat=_float(row.get("bodyfat")),
        percent_hydration=_float(row.get("water")),
        bone_mass=_float(row.get("bone")),
        skeletal_muscle_mass=round(weight * muscle_percent / 100, 2) if muscle_percent else None,
        visceral_fat_rating=round(visfat) if visfat else None,
        basal_met=_float(row.get("bmr")),
        metabolic_age=round(bodyage) if bodyage else None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, help="only look back this many days (default: full history)")
    parser.add_argument("--dry-run", action="store_true", help="only show what would be uploaded")
    parser.add_argument("--with-metabolic-age", action="store_true", help="also send metabolic age (Garmin shows it wrong)")
    args = parser.parse_args()

    since = datetime.now(timezone.utc) - timedelta(days=args.days) if args.days else datetime.min.replace(tzinfo=timezone.utc)
    period = f"in the last {args.days} days" if args.days else "in total"
    renpho = connect_renpho()
    try:
        rows = renpho.get_all_measurements(profile_user_id=load_profile_user_id())
    except (RenphoAPIError, RenphoSessionError) as error:
        print(f"Renpho session does not work ({error}). {RELOGIN_HINT}", file=sys.stderr)
        return 1
    candidates = sorted(
        (m for m in map(from_renpho, rows) if m and m.taken_at >= since),
        key=lambda m: m.taken_at,
    )
    if not candidates:
        print(f"Renpho: no weigh-ins {period}. Nothing to do.")
        return 0

    garmin = connect_garmin()
    start = candidates[0].taken_at.date() - timedelta(days=1)
    end = datetime.now(timezone.utc).date() + timedelta(days=1)
    existing = {entry.get("timestampGMT") for entry in fetch_weigh_ins(garmin, start, end)}
    new = [m for m in candidates if round(m.taken_at.timestamp() * 1000) not in existing]

    print(f"Renpho: {len(candidates)} weigh-ins {period}, {len(new)} new for Garmin.")
    for m in new:
        print(f"  {m.taken_at.astimezone():%Y-%m-%d %H:%M}  {m.weight:.2f} kg  fat {m.percent_fat}%")
    if not new or args.dry_run:
        return 0

    with tempfile.TemporaryDirectory() as folder:
        fit_path = Path(folder) / "renpho_sync.fit"
        fit_path.write_bytes(build_fit(new, args.with_metabolic_age))
        result = garmin.upload_activity(str(fit_path))
    failures = (result or {}).get("detailedImportResult", {}).get("failures") or []
    if failures:
        print(f"Garmin rejected the upload: {failures}", file=sys.stderr)
        return 1

    stored = {entry.get("timestampGMT") for entry in fetch_weigh_ins(garmin, start, end)}
    missing = [m for m in new if round(m.taken_at.timestamp() * 1000) not in stored]
    if missing:
        print(f"Uploaded, but Garmin does not show {len(missing)} of {len(new)} yet.", file=sys.stderr)
        return 1
    print(f"Uploaded {len(new)} weigh-ins to Garmin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
