#!/bin/sh
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
out=build/fullpaths-private-v2
test ! -e "$out/qualification.json"
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
if [ ! -e "$out/cores/combined.so" ]; then
 (cd "$out/combined-core";make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \
 CC="arm-linux-gnueabihf-gcc $flags" \
 SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
 LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1') > "$out/core-build.log" 2>&1
 cp "$out/combined-core/snes9x2005_plus_libretro.so" "$out/cores/combined.so"
fi
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so'
arm-linux-gnueabihf-gcc $flags -DD35_NATIVE_PCM -std=gnu99 -O3 -flto=4 -Wall -Wextra -Werror -Wno-misleading-indentation -no-pie -nostdlib \
 -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 "$out/main.c" "$out/runner/board.c" "$out/runner/runner.c" "$out/runner/audio-owner.c" \
 "$out/runner/native-pcm.c" "$out/runner/startup.c" "$out/runner/platform.c" "$out/runner/timing.c" \
 build/glibc230-stat-compat.c $libs -o "$out/ability-suite"
arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "$out/compare.c" $libs -o "$out/compare"
arm-linux-gnueabihf-readelf -V "$out/ability-suite" "$out/cores/combined.so" > "$out/abi.txt"
echo 'Built five-core measurement suite, all frames retained'
