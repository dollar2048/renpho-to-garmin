"""Convert a RENPHO Health CSV export into one Garmin body-composition .fit file.

Usage:
    .venv/bin/python renpho_to_fit.py "RENPHO Health-<name>.csv" -o renpho_weight.fit
    .venv/bin/python renpho_to_fit.py export.csv --since 2026-11-01 --last-per-day

Metabolic age is left out by default: Garmin Connect stores it as milliseconds
(age x 31,556,926,000) and shows that raw number as "years". Garmin Index scales
never send it either. Use --with-metabolic-age to include it anyway.
"""

import argparse
import csv
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.weight_scale_message import WeightScaleMessage
from fit_tool.profile.profile_type import FileType, Manufacturer


@dataclass(frozen=True)
class Measurement:
    taken_at: datetime  # timezone-aware
    weight: float
    bmi: float | None
    percent_fat: float | None
    percent_hydration: float | None
    bone_mass: float | None
    skeletal_muscle_mass: float | None
    visceral_fat_rating: int | None
    basal_met: float | None
    metabolic_age: int | None


def _num(value: str) -> float | None:
    value = value.strip()
    if not value or value == "--":
        return None
    return float(value)


def _int(value: str) -> int | None:
    number = _num(value)
    return None if number is None else round(number)


def read_renpho_csv(path: Path, tz: ZoneInfo) -> list[Measurement]:
    measurements = []
    with path.open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            weight = _num(row["Weight(kg)"])
            if weight is None:
                continue
            naive = datetime.strptime(f"{row['Date']} {row['Time']}", "%Y.%m.%d %H:%M:%S")
            measurements.append(
                Measurement(
                    taken_at=naive.replace(tzinfo=tz),
                    weight=weight,
                    bmi=_num(row["BMI"]),
                    percent_fat=_num(row["Body Fat Percentage(%)"]),
                    percent_hydration=_num(row["Body Water Percentage(%)"]),
                    bone_mass=_num(row["Bone Mass(kg)"]),
                    skeletal_muscle_mass=_num(row["Skeletal Muscle Mass(kg)"]),
                    visceral_fat_rating=_int(row["Visceral Fat"]),
                    basal_met=_num(row["BMR(kcal)"]),
                    metabolic_age=_int(row["Metabolic Age"]),
                )
            )
    measurements.sort(key=lambda m: m.taken_at)
    return measurements


def keep_last_per_day(measurements: list[Measurement]) -> list[Measurement]:
    by_day: dict[date, Measurement] = {}
    for m in measurements:  # sorted ascending, so the last one wins
        by_day[m.taken_at.date()] = m
    return list(by_day.values())


def system_time_zone() -> ZoneInfo:
    """IANA zone from /etc/localtime, so DST is applied per date (a fixed UTC offset would not)."""
    target = os.path.realpath("/etc/localtime")
    if "zoneinfo/" not in target:
        raise SystemExit("Cannot detect system time zone, pass --tz (e.g. --tz Europe/Berlin)")
    return ZoneInfo(target.split("zoneinfo/", 1)[1])


def _ms(moment: datetime) -> int:
    """fit-tool expects Unix time in milliseconds and converts to the FIT epoch itself."""
    return round(moment.timestamp() * 1000)


def build_fit(measurements: list[Measurement], with_metabolic_age: bool = False) -> bytes:
    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    file_id = FileIdMessage()
    file_id.type = FileType.WEIGHT
    file_id.manufacturer = Manufacturer.DEVELOPMENT.value
    file_id.product = 0
    file_id.serial_number = 0x52454E50  # "RENP"
    file_id.time_created = _ms(datetime.now(timezone.utc))
    builder.add(file_id)

    for m in measurements:
        message = WeightScaleMessage()
        message.timestamp = _ms(m.taken_at)
        message.weight = m.weight
        if m.bmi is not None:
            message.bmi = m.bmi
        if m.percent_fat is not None:
            message.percent_fat = m.percent_fat
        if m.percent_hydration is not None:
            message.percent_hydration = m.percent_hydration
        if m.bone_mass is not None:
            message.bone_mass = m.bone_mass
        # Garmin Connect shows the FIT `muscle_mass` field as "Skeletal Muscle Mass".
        if m.skeletal_muscle_mass is not None:
            message.muscle_mass = m.skeletal_muscle_mass
        if m.visceral_fat_rating is not None:
            message.visceral_fat_rating = m.visceral_fat_rating
        if m.basal_met is not None:
            message.basal_met = m.basal_met
        if with_metabolic_age and m.metabolic_age is not None:
            message.metabolic_age = m.metabolic_age
        builder.add(message)

    return builder.build().to_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", type=Path, help="RENPHO Health CSV export")
    parser.add_argument("-o", "--output", type=Path, default=Path("renpho_weight.fit"))
    parser.add_argument("--tz", default=None, help="IANA time zone of the RENPHO times, e.g. Europe/Berlin (default: system)")
    parser.add_argument("--since", type=date.fromisoformat, help="only measurements on or after this date (YYYY-MM-DD)")
    parser.add_argument("--until", type=date.fromisoformat, help="only measurements on or before this date (YYYY-MM-DD)")
    parser.add_argument("--last-per-day", action="store_true", help="keep only the last measurement of each day")
    parser.add_argument("--with-metabolic-age", action="store_true", help="also send metabolic age (Garmin shows it wrong)")
    args = parser.parse_args()

    tz = ZoneInfo(args.tz) if args.tz else system_time_zone()
    measurements = read_renpho_csv(args.csv, tz)
    if args.since:
        measurements = [m for m in measurements if m.taken_at.date() >= args.since]
    if args.until:
        measurements = [m for m in measurements if m.taken_at.date() <= args.until]
    if args.last_per_day:
        measurements = keep_last_per_day(measurements)
    if not measurements:
        print("No measurements to write.", file=sys.stderr)
        return 1

    args.output.write_bytes(build_fit(measurements, args.with_metabolic_age))
    first, last = measurements[0].taken_at, measurements[-1].taken_at
    print(f"Wrote {len(measurements)} measurements ({first:%Y-%m-%d} .. {last:%Y-%m-%d}) to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
