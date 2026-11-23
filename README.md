# renpho-to-garmin

Move RENPHO scale history (weight, body fat, muscle, bone, water, visceral fat) to Garmin Connect as real body-composition weigh-ins.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

1. Export CSV from the RENPHO app.
2. Log in to Garmin once (tokens are saved in `~/.garminconnect`):
   ```bash
   .venv/bin/python garmin_login.py
   ```
3. Convert CSV to FIT:
   ```bash
   .venv/bin/python renpho_to_fit.py "RENPHO Health-<name>.csv" -o renpho_weight.fit
   ```
4. Upload:
   ```bash
   .venv/bin/python garmin_upload.py renpho_weight.fit
   ```

Optional: list or delete old weigh-ins (delete asks for confirmation):

```bash
.venv/bin/python garmin_weighins.py list   --start 2023-01-01 --end 2026-12-31
.venv/bin/python garmin_weighins.py delete --start 2023-01-01 --end 2026-12-31 --source MANUAL
```

## Notes

- Metabolic age is off by default: Garmin Connect web shows it as milliseconds
  ([forum report](https://forums.garmin.com/de/apps-und-software/mobile-apps-web/f/garmin-connect-mobile-web/447842/metabolic_age-unit-conversion-issue-in-garmin-connect-website)).
  Use `--with-metabolic-age` to send it anyway.
- CSV, FIT and token files are in `.gitignore`. Keep your CSV backup yourself.
