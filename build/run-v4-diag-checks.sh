#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
mkdir -p v4-diagnostic/verification
cd v4-diagnostic/verification
export D35_DIAG_INTERVAL_MS=100
export D35_TIMING_LOG="$base/v4-diagnostic/verification/timing.log"
export D35_PLUS_LOG="$base/v4-diagnostic/verification/adapter.log"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v4-diagnostic/video-contract-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v4-diagnostic/adapter-check-arm"
export D35_PLUS_CORE="$base/v4-diagnostic/emu_sfc_plus.so" D35_TEST_HEAP_VIDEO=1
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/v4-diagnostic:$base/sysroot/lib" \
 "$base/v4-diagnostic/harness-arm" "$base/ff3.zip"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v4-diagnostic/audio-diagnostics-check-arm"
