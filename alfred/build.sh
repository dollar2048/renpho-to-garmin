#!/bin/bash
# Pack the Alfred workflow into dist/Renpho-Garmin-Sync.alfredworkflow (double-click to install).
set -euo pipefail
cd "$(dirname "$0")"
plutil -lint info.plist >/dev/null
chmod +x run_sync.sh
mkdir -p ../dist
rm -f ../dist/Renpho-Garmin-Sync.alfredworkflow
zip -q -X ../dist/Renpho-Garmin-Sync.alfredworkflow info.plist run_sync.sh
echo "Built dist/Renpho-Garmin-Sync.alfredworkflow"
