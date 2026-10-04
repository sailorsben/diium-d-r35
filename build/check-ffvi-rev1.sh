#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
base=$(pwd)
mkdir -p SNES-comparison-FFVI-Rev1/verification
cd SNES-comparison-FFVI-Rev1/verification
unset D35_PLUS_LOG
export D35_PLUS_CORE="$base/build/clean/emu_sfc_plus.so" D35_TEST_HEAP_VIDEO=1
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/clean:$base/build/sysroot/lib" "$base/build/clean/harness-arm" "$base/SNES-comparison-FFVI-Rev1/Final Fantasy VI (Rev 1).zip" > checks.log 2>&1
cat checks.log
