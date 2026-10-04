#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
mkdir -p v8-capture/verification
cd v8-capture/verification
export D35_DIAG_INTERVAL_MS=100
export D35_CAPTURE_DIRECTORY="$base/v8-capture/verification"
export D35_TIMING_LOG="$base/v8-capture/verification/timing.log"
export D35_PLUS_LOG="$base/v8-capture/verification/adapter.log"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v8-capture/video-contract-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v8-capture/adapter-check-arm"
export D35_PLUS_CORE="$base/v8-capture/emu_sfc_plus.so" D35_TEST_HEAP_VIDEO=1
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/v8-capture:$base/sysroot/lib" \
 "$base/v8-capture/harness-arm" "$base/ff3.zip"
mkdir -p display-enabled
cd display-enabled
export D35_CAPTURE_DIRECTORY="$base/v8-capture/verification/display-enabled"
export D35_TIMING_LOG="$base/v8-capture/verification/display-enabled/timing.log"
export D35_PLUS_LOG="$base/v8-capture/verification/display-enabled/adapter.log"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/v8-capture:$base/sysroot/lib" \
 "$base/v8-capture/harness-arm" "$base/ff3.zip" display-test
cd ..
mkdir -p capture-mock
cd capture-mock
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v8-capture/audio-diagnostics-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/v8-capture/audio-write-audit-check-arm"
