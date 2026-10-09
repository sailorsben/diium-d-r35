#!/bin/sh
# Passive consumed-once inventory. No vendor tool execution or device controls.
BASE=${D35_SURVEY_BASE:-/usr/retro/device-survey}
ROOT=${D35_SURVEY_ROOT:-/}
[ -f "$BASE/armed" ] || exit 0
mv "$BASE/armed" "$BASE/consumed" || exit 1
sync
exec > "$BASE/startup.log" 2>&1
printf 'suite=device-survey-1 mode=passive marker_consumed=1\n'
export LD_LIBRARY_PATH=/lib:/usr/lib:/system/lib:/usr/retro/libs
"$BASE/device-survey" "$ROOT" "$BASE/results" 30
STATUS=$?
printf 'survey_exit=%s\n' "$STATUS"
sync
exit "$STATUS"
