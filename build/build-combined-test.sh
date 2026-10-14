#!/bin/sh
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
out=build/combined-test-private-v1
test ! -e "$out/qualification.json"
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so'
arm-linux-gnueabihf-gcc $flags -DD35_NATIVE_PCM -std=gnu99 -O3 -flto=4 -Wall -Wextra -Werror -Wno-misleading-indentation -no-pie -nostdlib \
 -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 "$out/main.c" "$out/runner/board.c" "$out/runner/runner.c" "$out/runner/audio-owner.c" \
 "$out/runner/native-pcm.c" "$out/runner/startup.c" "$out/runner/platform.c" "$out/runner/timing.c" \
 build/glibc230-stat-compat.c $libs -o "$out/ability-suite"
arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "build/fullpaths-private-v2/compare.c" $libs -o "$out/compare"
arm-linux-gnueabihf-readelf -V "$out/ability-suite" "$out/cores/combined.so" > "$out/abi.txt"
echo 'Built three-core combined measurement suite, all frames retained'
