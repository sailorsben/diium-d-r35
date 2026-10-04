#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
mkdir -p v6-capture/verification
cd v6-capture/verification
export D35_DIAG_INTERVAL_MS=100
export D35_CAPTURE_DIRECTORY="$base/v6-capture/verification"
export D35_TIMING_LOG="$base/v6-capture/verification/timing.log"
export D35_PLUS_LOG="$base/v6-capture/verification/adapter.log"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v6-capture/video-contract-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v6-capture/adapter-check-arm"
export D35_PLUS_CORE="$base/v6-capture/emu_sfc_plus.so" D35_TEST_HEAP_VIDEO=1
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/v6-capture:$base/sysroot/lib" \
 "$base/v6-capture/harness-arm" "$base/ff3.zip"
mkdir -p capture-mock
cd capture-mock
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v6-capture/audio-diagnostics-check-arm"
