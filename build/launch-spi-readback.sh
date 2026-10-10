#!/bin/sh
# Synchronous: stock starts only after the owned SPI reader exits.
BASE=${D35_READBACK_BASE:-/usr/retro/spi-readback}
ROOT=${D35_READBACK_ROOT:-/}
[ -f "$BASE/armed" ] || exit 0
mv "$BASE/armed" "$BASE/consumed" || exit 1
sync
exec > "$BASE/startup.log" 2>&1
printf 'suite=spi-readback-1 marker_consumed=1 fixed_read_commands=05,9f,03\n'
export LD_LIBRARY_PATH=/lib:/usr/lib:/system/lib:/usr/retro/libs
"$BASE/spi-readback" "$ROOT" "$BASE/results"
STATUS=$?
printf 'readback_exit=%s\n' "$STATUS"
sync
exit "$STATUS"
