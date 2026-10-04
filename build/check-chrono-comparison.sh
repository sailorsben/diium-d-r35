#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
comparison_root=$(pwd)
mkdir -p SNES-comparison-Chrono-Trigger/verification
cd SNES-comparison-Chrono-Trigger/verification
unset D35_PLUS_LOG
export D35_PLUS_CORE="$comparison_root/build/clean/emu_sfc_plus.so" D35_TEST_HEAP_VIDEO=1
qemu-arm -cpu cortex-a7 -L "$comparison_root/build/sysroot" \
 -E LD_LIBRARY_PATH="$comparison_root/build/clean:$comparison_root/build/sysroot/lib" \
 "$comparison_root/build/clean/harness-arm" "$comparison_root/SNES-comparison-Chrono-Trigger/Chrono Trigger.zip" > checks.log 2>&1
