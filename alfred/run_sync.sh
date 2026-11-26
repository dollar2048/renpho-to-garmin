#!/bin/bash
# Alfred "renpho" keyword: sync new Renpho weigh-ins to Garmin Connect.
#   renpho         -> sync everything that is missing in Garmin (full history)
#   renpho dry     -> dry run, upload nothing
#   renpho 30      -> only look at the last 30 days
#   renpho 30 dry  -> both
# Prints one short line for the Alfred notification; the full log goes to LOG_FILE.

# project_dir comes from the workflow configuration in Alfred (not stored in this repo).
project_dir="${project_dir/#\~/$HOME}"
LOG_FILE="$HOME/Library/Logs/renpho-garmin-sync.log"

if [[ -z "$project_dir" ]]; then
  echo "Set 'Project folder' in the workflow configuration in Alfred"
  exit 0
fi

if [[ ! -x "$project_dir/.venv/bin/python" ]]; then
  echo "Project not found: $project_dir (set project_dir in the workflow configuration)"
  exit 0
fi

# Accept "dry" and/or a number of days in any order ("30 dry", "dry 30").
# Anything else stops here, so a typo never turns a dry run into a real upload.
args=()
query="${1:-}"
for word in $query; do
  if [[ "$word" == "dry" ]]; then
    args+=(--dry-run)
  elif [[ "$word" =~ ^[0-9]+$ ]]; then
    args+=(--days "$word")
  else
    printf '❌ Unknown input: %s\n\nUse: renpho | renpho dry | renpho 30 | renpho 30 dry\nNothing was run.\n' "$word"
    exit 0
  fi
done

cd "$project_dir" || exit 0
output="$(.venv/bin/python renpho_garmin_sync.py "${args[@]}" 2>&1)"
status=$?
{ echo "=== $(date '+%Y-%m-%d %H:%M:%S') renpho ${query} (exit $status)"; echo "$output"; } >> "$LOG_FILE"

# Shown in Alfred Large Type (stays until you click or press a key), so keep line breaks.
# Skip library log lines (they start with a date); keep at most 15 lines.
if [[ $status -eq 0 ]]; then
  title="✅ Renpho → Garmin"
  [[ " ${args[*]} " == *" --dry-run "* ]] && title="🔍 Renpho → Garmin (dry run)"
else
  title="❌ Renpho → Garmin failed"
fi
body="$(echo "$output" | grep -v -E '^[0-9]{4}-[0-9]{2}-[0-9]{2} ' | head -n 15)"
printf '%s\n\n%s\n' "$title" "${body:-Done.}"
[[ $status -ne 0 ]] && printf '\nLog: ~/Library/Logs/renpho-garmin-sync.log\n'
exit 0
