# renpho-to-garmin

Move RENPHO scale history (weight, body fat, muscle, bone, water, visceral fat) to Garmin Connect as real body-composition weigh-ins.

Two ways:

- **Automatic sync** from Renpho Cloud, started with one Alfred keyword (or one command).
- **Manual import** of a RENPHO CSV export.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Log in once to both services (run in a terminal, the scripts ask for input; passwords are not stored):

```bash
.venv/bin/python garmin_login.py   # tokens -> Keychain item "renpho-to-garmin.garmin"
.venv/bin/python renpho_login.py   # session + chosen profile -> Keychain item "renpho-to-garmin.renpho"
```

Tokens live in the macOS login Keychain (via [keyring](https://github.com/jaraco/keyring)), not in files in your home folder. You can see or delete them in Keychain Access. After a Python upgrade macOS may ask once to allow access: choose "Always Allow". Running a login script again replaces the saved tokens.

`renpho_login.py` lists all measurement profiles of the Renpho account (family members) and asks which one goes to Garmin.

## Automatic sync (Renpho Cloud)

```bash
.venv/bin/python renpho_garmin_sync.py --dry-run   # show what would be uploaded
.venv/bin/python renpho_garmin_sync.py             # upload
.venv/bin/python renpho_garmin_sync.py --days 30   # only look at the last 30 days
```

The script compares the full Renpho history with Garmin by exact timestamp and uploads only weigh-ins that are missing in Garmin, as one FIT file. Then it checks that Garmin stored them. Running it again is safe: nothing is uploaded twice, and a weigh-in missed by an earlier run is picked up later.

## Alfred workflow

1. Build the workflow:
   ```bash
   alfred/build.sh   # -> dist/Renpho-Garmin-Sync.alfredworkflow
   ```
2. Double-click `dist/Renpho-Garmin-Sync.alfredworkflow` and import it into Alfred.
3. In the workflow configuration set **Project folder** to this repository folder, e.g. `~/path/to/renpho-to-garmin`.
   It is stored in Alfred, not in the repository.
4. Do the two logins from [Setup](#setup) once.

Keywords:

| Alfred input | What it does |
|---|---|
| `renpho` | Upload every weigh-in that is missing in Garmin |
| `renpho dry` | Show what would be uploaded, upload nothing |
| `renpho 30` | Only look at the last 30 days |

The result comes as a macOS notification. Full log: `~/Library/Logs/renpho-garmin-sync.log`.

After changing files in `alfred/`, run `alfred/build.sh` again and re-import. Changes to the Python scripts need no rebuild: the workflow runs them from the project folder.

## Manual import (CSV)

1. Export CSV from the RENPHO app.
2. Convert CSV to FIT:
   ```bash
   .venv/bin/python renpho_to_fit.py "RENPHO Health-<name>.csv" -o renpho_weight.fit
   ```
   Options: `--since` / `--until YYYY-MM-DD`, `--last-per-day`, `--tz Europe/Berlin` (default: system time zone).
3. Upload:
   ```bash
   .venv/bin/python garmin_upload.py renpho_weight.fit
   ```

Optional: list or delete old weigh-ins (delete asks for a typed confirmation):

```bash
.venv/bin/python garmin_weighins.py list   --start 2023-01-01 --end 2026-12-31
.venv/bin/python garmin_weighins.py delete --start 2023-01-01 --end 2026-12-31 --source MANUAL
```

Uploaded weigh-ins have source `INDEX_SCALE` in Garmin; old Garmin CSV imports have source `MANUAL`.

## Notes

- Metabolic age is off by default: Garmin Connect web shows it as milliseconds
  ([forum report](https://forums.garmin.com/de/apps-und-software/mobile-apps-web/f/garmin-connect-mobile-web/447842/metabolic_age-unit-conversion-issue-in-garmin-connect-website)).
  Use `--with-metabolic-age` to send it anyway.
- Skeletal muscle mass for Garmin is computed as `weight × skeletal muscle %` (Renpho Cloud sends the percentage).
- When a login expires, the sync says so; run `garmin_login.py` or `renpho_login.py` again.
- Both Garmin Connect and Renpho Cloud APIs are unofficial ([python-garminconnect](https://github.com/cyberjunky/python-garminconnect), [renpho-py](https://github.com/ChocoTonic/renpho-py)) and may break when the services change.
- CSV, FIT and JSON files are in `.gitignore`. Keep your CSV backup yourself.
