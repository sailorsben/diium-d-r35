#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
mkdir -p comparison-2010/verification
cd comparison-2010/verification
unset D35_PLUS_LOG
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" "$base/comparison-2010/video-contract-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" "$base/comparison-2010/adapter-check-arm"
export D35_2010_CORE="$base/comparison-2010/emu_sfc_2010.so" D35_TEST_HEAP_VIDEO=1
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/comparison-2010:$base/sysroot/lib" "$base/comparison-2010/harness-arm" "$base/ff3.zip"
