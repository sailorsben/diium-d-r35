#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
mkdir -p verification-path
cd verification-path
export D35_PLUS_CORE="$base/emu_sfc_plus.so"
export D35_PLUS_LOG="$base/verification-path/adapter.log"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base:$base/sysroot/lib" \
 "$base/harness-arm" "$base/ff3.zip"
