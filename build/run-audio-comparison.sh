#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -no-pie -nostdlib \
 -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 capture-audio.c -L./sysroot/lib -Wl,--no-as-needed \
 -l:libdl-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -o capture-audio-arm
mkdir -p audio-comparison/plus-native audio-comparison/plus-adapter audio-comparison/2010-native
if [ "${1:-}" != "2010-only" ]; then
cd audio-comparison/plus-native
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/capture-audio-arm" "$base/emu_sfc_plus.so" "$base/ff3.smc" 9000
cd "$base/audio-comparison/plus-adapter"
export D35_PLUS_CORE="$base/emu_sfc_plus.so" D35_PLUS_LOG="$base/audio-comparison/plus-adapter/adapter.log" D35_TEST_HEAP_VIDEO=1
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/capture-audio-arm" "$base/v2/emu_sfc.so" "$base/ff3.smc" 9000
fi
cd "$base/audio-comparison/2010-native"
qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \
 "$base/capture-audio-arm" "$base/compare-2010.so" "$base/ff3.smc" 9000
