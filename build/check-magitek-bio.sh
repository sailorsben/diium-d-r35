#!/bin/sh
# Actual game effect equivalence. State/ROM remain private and owner supplied.
set -eu
test "$#" -eq 1
BASE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
test -f "$1"
qemu-arm -cpu cortex-a7 -L "$BASE/sysroot" -E LD_LIBRARY_PATH="$BASE/sysroot/lib" \
 "$BASE/plus-a7-out/equivalence" "$BASE/clean/emu_sfc_plus.so" "$BASE/plus-a7-out/plus-a7.so" \
 "$BASE/plus-a7-out/ff6.sfc" "$1" 1200 magitek-bio > "$BASE/plus-a7-out/magitek-bio-equivalence.log"
cat "$BASE/plus-a7-out/magitek-bio-equivalence.log"
