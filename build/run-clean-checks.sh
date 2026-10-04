#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
mkdir -p clean/verification
cd clean/verification
unset D35_PLUS_LOG
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/clean/video-contract-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/clean/adapter-check-arm"
export D35_PLUS_CORE="$base/clean/emu_sfc_plus.so" D35_TEST_HEAP_VIDEO=1
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/clean:$base/sysroot/lib" \
 "$base/clean/harness-arm" "$base/ff3.zip"
