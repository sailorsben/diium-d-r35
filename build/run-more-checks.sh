#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
mkdir -p verification-audio verification-memory verification-raw
cd verification-audio
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" "$base/adapter-check-arm"
cd "$base/verification-memory"
export D35_PLUS_CORE="$base/emu_sfc_plus.so" D35_PLUS_LOG="$base/verification-memory/adapter.log"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base:$base/sysroot/lib" \
 "$base/harness-arm" "$base/ff3.zip" memory
cd "$base/verification-raw"
export D35_PLUS_LOG="$base/verification-raw/adapter.log"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base:$base/sysroot/lib" \
 "$base/harness-arm" "$base/ff3.smc" memory
