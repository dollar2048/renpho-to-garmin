"""List or delete Garmin Connect weigh-ins in a date range.

`list` only reads. `delete` shows the same list and deletes only after you type the confirmation phrase.

Usage:
    .venv/bin/python garmin_weighins.py list   --start 2023-05-16 --end 2026-11-23
    .venv/bin/python garmin_weighins.py list   --start 2026-11-01 --end 2026-11-23 --raw
    .venv/bin/python garmin_weighins.py delete --start 2023-05-16 --end 2026-11-23 --source MANUAL
"""

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any

from garmin_client import connect

CHUNK_DAYS = 90  # keep each range request small; Garmin limits are not documented


def fetch_weigh_ins(api, start: date, end: date) -> list[dict[str, Any]]:
    by_pk: dict[Any, dict[str, Any]] = {}
    chunk_start = start
    while chunk_start <= end:
        chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS - 1), end)
        response = api.get_weigh_ins(chunk_start.isoformat(), chunk_end.isoformat()) or {}
        for summary in response.get("dailyWeightSummaries", []):
            for entry in summary.get("allWeightMetrics", []):
                by_pk[entry.get("samplePk")] = entry
        for entry in response.get("dateWeightList", []):  # other response shape, just in case
            by_pk[entry.get("samplePk")] = entry
        chunk_start = chunk_end + timedelta(days=1)
    return sorted(by_pk.values(), key=lambda e: e.get("timestampGMT") or e.get("date") or 0)


def _kg(grams: Any) -> str:
    return "--" if grams is None else f"{grams / 1000:.2f}"


def _when(entry: dict[str, Any]) -> str:
    millis = entry.get("timestampGMT") or entry.get("date")
    if millis is None:
        return str(entry.get("calendarDate"))
    return datetime.fromtimestamp(millis / 1000, timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


def print_summary(entries: list[dict[str, Any]], show_rows: int) -> None:
    sources = Counter(entry.get("sourceType", "?") for entry in entries)
    print(f"Found {len(entries)} weigh-ins")
    for source, count in sources.most_common():
        print(f"  {source:<20} {count}")
    if not entries:
        return
    print(f"\n{'local time':<17} {'source':<14} {'kg':>6} {'fat%':>5} {'water%':>6} {'bone':>5} {'muscle':>6}")
    rows = entries if show_rows <= 0 or len(entries) <= show_rows else entries[:show_rows // 2] + [None] + entries[-show_rows // 2:]
    for entry in rows:
        if entry is None:
            print("  ...")
            continue
        print(
            f"{_when(entry):<17} {str(entry.get('sourceType', '?')):<14} {_kg(entry.get('weight')):>6} "
            f"{entry.get('bodyFat') or '--':>5} {entry.get('bodyWater') or '--':>6} "
            f"{_kg(entry.get('boneMass')):>5} {_kg(entry.get('muscleMass')):>6}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["list", "delete"])
    parser.add_argument("--start", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    parser.add_argument("--source", action="append", help="only this sourceType (repeatable), e.g. MANUAL")
    parser.add_argument("--rows", type=int, default=20, help="rows to print, 0 = all")
    parser.add_argument("--raw", action="store_true", help="print the first raw entry as JSON")
    args = parser.parse_args()

    api = connect()
    entries = fetch_weigh_ins(api, args.start, args.end)
    if args.source:
        entries = [entry for entry in entries if entry.get("sourceType") in args.source]

    print_summary(entries, args.rows)
    if args.raw and entries:
        print("\nFirst raw entry:\n" + json.dumps(entries[0], indent=2, ensure_ascii=False))

    if args.command == "list" or not entries:
        return 0

    phrase = f"delete {len(entries)}"
    print(f"\nThis permanently deletes {len(entries)} weigh-ins from Garmin Connect. It cannot be undone.")
    if input(f'Type "{phrase}" to continue: ').strip() != phrase:
        print("Cancelled, nothing deleted.")
        return 1

    failed = 0
    for number, entry in enumerate(entries, 1):
        try:
            api.delete_weigh_in(entry["samplePk"], entry["calendarDate"])
        except Exception as error:  # keep going, report at the end
            failed += 1
            print(f"  failed {_when(entry)}: {error}", file=sys.stderr)
        if number % 50 == 0:
            print(f"  {number}/{len(entries)}")
    print(f"Deleted {len(entries) - failed}, failed {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
