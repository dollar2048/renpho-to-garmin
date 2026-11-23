#!/bin/bash
# Alfred "renpho" keyword: sync new Renpho weigh-ins to Garmin Connect.
#   renpho         -> sync everything that is missing in Garmin (full history)
#   renpho dry     -> dry run, upload nothing
#   renpho 30      -> only look at the last 30 days
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

args=()
query="$(echo "${1:-}" | tr -d '[:space:]')"
if [[ "$query" == "dry" ]]; then
  args+=(--dry-run)
elif [[ "$query" =~ ^[0-9]+$ ]]; then
  args+=(--days "$query")
fi

cd "$project_dir" || exit 0
output="$(.venv/bin/python renpho_garmin_sync.py "${args[@]}" 2>&1)"
status=$?
{ echo "=== $(date '+%Y-%m-%d %H:%M:%S') renpho ${query} (exit $status)"; echo "$output"; } >> "$LOG_FILE"

if [[ $status -eq 0 ]]; then
  summary="$(echo "$output" | grep -E '^(Renpho:|Uploaded)' | tail -n 2 | tr '\n' ' ')"
  echo "${summary:-Done.}"
else
  echo "Failed: $(echo "$output" | tail -n 1) (log: ~/Library/Logs/renpho-garmin-sync.log)"
fi
