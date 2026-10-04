#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
base=$(pwd)
out="$base/build/production/verification"
mkdir -p "$out/control" "$out/test" "$out/state"
export D35_PLUS_CORE="$base/build/clean/emu_sfc_plus.so" D35_TEST_HEAP_VIDEO=1
unset D35_PLUS_LOG D35_V10_FORCE_HALF_RENDER D35_V10_DISABLE
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" "$base/build/production/check-arm"
export D35_V10_DISABLE=1
cd "$out/control"
export D35_V10_REPORT="$PWD/should-not-exist.txt"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" "$base/build/production/capture-arm" "$base/build/production/emu_sfc.so" "$base/build/ff3.smc" 4200 > checks.log 2>&1
unset D35_V10_DISABLE
export D35_V10_FORCE_HALF_RENDER=1
cd "$out/test"
export D35_V10_REPORT="$PWD/should-not-exist.txt"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" "$base/build/production/capture-arm" "$base/build/production/emu_sfc.so" "$base/build/ff3.smc" 4200 > checks.log 2>&1
cmp "$out/control/native.s16le" "$out/test/native.s16le"
cmp "$out/control/batches.csv" "$out/test/batches.csv"
test ! -e "$out/control/should-not-exist.txt"
test ! -e "$out/test/should-not-exist.txt"
cat "$out/control/checks.log" "$out/test/checks.log"
printf 'PASS: exact PCM and callback history with half rendering, no automatic reports\n'
unset D35_V10_FORCE_HALF_RENDER
cd "$out/state"
export D35_V10_REPORT="$PWD/should-not-exist.txt"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/production:$base/build/sysroot/lib" "$base/build/clean/harness-arm" "$base/build/ff3.smc"
test ! -e "$out/state/should-not-exist.txt"
