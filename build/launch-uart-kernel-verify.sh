#!/bin/sh
# One-shot, before stock SPI ownership. Fixed reader never programs flash.
BASE=/usr/retro/uart-kernel-verify1
[ -f "$BASE/armed" ] || exit 0
mv "$BASE/armed" "$BASE/consumed" || exit 64
sync
exec > "$BASE/wrapper.log" 2>&1
printf 'suite=uart-kernel-verify1 flash_writes=0 module_loads=0\n'
export LD_LIBRARY_PATH=/lib:/usr/lib:/system/lib:/usr/retro/libs
mkdir -p "$BASE/logs" || exit 64
"$BASE/uart-observe" / "$BASE/logs/uart-before" || exit 64
"$BASE/spi-readback" / "$BASE/results"
result=$?
printf 'readback_exit=%s\n' "$result"
[ "$result" -eq 0 ] || exit 64
"$BASE/uart-observe" / "$BASE/logs/uart-after" || exit 64
printf 'verification_exit=0 owned_reader_reaped=1\n'
sync
exit 0
