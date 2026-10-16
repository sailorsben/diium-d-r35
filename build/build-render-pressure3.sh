#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=build/render-pressure3-private
flags='-DD35_PLUS_A7 -DD35_NATIVE_PCM -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -Ibuild -I"$out/runner" -Ibuild/snes9x2005/libretro-common/include \
 -MM build/render-pressure3.c > "$out/render-dependencies.txt"
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O3 -Wall -Wextra -Werror -Wno-misleading-indentation -no-pie -nostdlib \
 -Ibuild -I"$out/runner" -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 build/render-pressure3.c "$out/runner/board.c" "$out/runner/audio-owner.c" "$out/runner/native-pcm.c" \
 "$out/runner/startup.c" "$out/runner/platform.c" "$out/runner/timing.c" \
 -Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libpthread-2.30.so -l:librt-2.30.so \
 -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so -o "$out/render-pressure"
arm-linux-gnueabihf-readelf -V "$out/render-pressure" > "$out/abi.txt"
arm-linux-gnueabihf-objdump -d "$out/render-pressure" > "$out/disassembly.txt"
arm-linux-gnueabihf-size "$out/render-pressure"
