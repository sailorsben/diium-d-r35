#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
base=$(pwd)
out="$base/device-evidence/ff6-deep-review/core-render-control"
flags='-marm -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=c99 -O2 -Wall -Wextra -fPIC -shared -nostdlib -Wl,--no-undefined -Wl,-Bsymbolic-functions -I"$base/build/snes9x2005/libretro-common/include" "$out/adapter-render-control.c" -L"$base/build/sysroot/lib" -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o "$out/adapter-render-control.so"
export D35_PLUS_CORE="$base/build/clean/emu_sfc_plus.so" D35_TEST_HEAP_VIDEO=1
unset D35_PLUS_LOG D35_TEST_SKIP_CORE_RENDER
mkdir -p "$out/render-on" "$out/render-off"
cd "$out/render-on"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" "$base/build/capture-audio-arm" "$out/adapter-render-control.so" "$base/build/ff3.smc" 9000 > checks.log 2>&1
export D35_TEST_SKIP_CORE_RENDER=1
cd "$out/render-off"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" "$base/build/capture-audio-arm" "$out/adapter-render-control.so" "$base/build/ff3.smc" 9000 > checks.log 2>&1
cmp "$out/render-on/native.s16le" "$out/render-off/native.s16le"
cmp "$out/render-on/batches.csv" "$out/render-off/batches.csv"
cat "$out/render-on/checks.log" "$out/render-off/checks.log"
printf 'PASS: Same PCM and audio callback sizes with core rendering disabled\n'
