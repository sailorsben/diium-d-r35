#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
base=$(pwd)
out="$base/build/v10-budget/verification"
mkdir -p "$out/control" "$out/test" "$out/state"
export D35_PLUS_CORE="$base/build/clean/emu_sfc_plus.so" D35_TEST_HEAP_VIDEO=1
unset D35_PLUS_LOG
cd "$out"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" "$base/build/v10-budget/check-arm"
export D35_V10_DISABLE=1
cd "$out/control"
export D35_V10_REPORT="$PWD/report.txt"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" "$base/build/capture-audio-arm" "$base/build/v10-budget/emu_sfc.so" "$base/build/ff3.smc" 4200 > checks.log 2>&1
unset D35_V10_DISABLE
export D35_V10_FORCE_HALF_RENDER=1
cd "$out/test"
export D35_V10_REPORT="$PWD/report.txt"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" "$base/build/capture-audio-arm" "$base/build/v10-budget/emu_sfc.so" "$base/build/ff3.smc" 4200 > checks.log 2>&1
cmp "$out/control/native.s16le" "$out/test/native.s16le"
cmp "$out/control/batches.csv" "$out/test/batches.csv"
cat "$out/control/checks.log" "$out/test/checks.log"
printf 'PASS: scheduled core-render disable preserves exact PCM and audio callback sizes\n'
unset D35_V10_FORCE_HALF_RENDER
cd "$out/state"
export D35_V10_REPORT="$PWD/report.txt"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/v10-budget:$base/build/sysroot/lib" "$base/build/clean/harness-arm" "$base/build/ff3.smc"
