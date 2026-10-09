#!/bin/sh
# Synchronous early boot: never compete with stock vrtemu's open SPI descriptor.
BASE=${D35_SPI_BASE:-/usr/retro/spi-identify}
ROOT=${D35_SPI_ROOT:-/}
[ -f "$BASE/armed" ] || exit 0
mv "$BASE/armed" "$BASE/consumed" || exit 1
sync
exec > "$BASE/startup.log" 2>&1
printf 'suite=spi-identify-1 marker_consumed=1 fixed_read_commands=05,9f\n'
export LD_LIBRARY_PATH=/lib:/usr/lib:/system/lib:/usr/retro/libs
"$BASE/spi-identify" "$ROOT" "$BASE/results"
STATUS=$?
printf 'identify_exit=%s\n' "$STATUS"
sync
exit "$STATUS"
