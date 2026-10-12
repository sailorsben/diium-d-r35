#!/bin/sh
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
out=build/a7-pair-private-v1
if [ "${D35_PAIR_RESUME:-0}" = 1 ];then
 test -f "$out/prepared.json";test ! -f "$out/verification.json"
else
 python3 build/prepare-a7-pair.py
fi
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so'
if [ ! -f "$out/core/snes9x2005_plus_libretro.so" ];then
 (cd "$out/core";make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \
 CC="arm-linux-gnueabihf-gcc $flags" \
 SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
 LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1' > ../core-build.log 2>&1)
fi
arm-linux-gnueabihf-gcc $flags -DD35_NATIVE_PCM -std=gnu99 -O3 -flto=4 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 build/a7-pair-main.c "$out/runner/board.c" "$out/runner/runner.c" "$out/runner/audio-owner.c" \
 "$out/runner/native-pcm.c" "$out/runner/startup.c" "$out/runner/platform.c" "$out/runner/timing.c" \
 build/glibc230-stat-compat.c $libs -o "$out/pair-suite"
arm-linux-gnueabihf-readelf -V "$out/pair-suite" > "$out/runner-abi.txt"
for which in equivalence replay;do
 arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 "$out/$which.c" $libs -o "$out/$which"
done
qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib \
 "$out/equivalence" build/plus-a7-out/plus-a7.so "$out/core/snes9x2005_plus_libretro.so" \
 build/plus-a7-out/ff6.sfc build/magitek-bio-private/scene.state 1200 magitek-bio > "$out/equivalence-bio.log"
qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib \
 "$out/equivalence" build/plus-a7-out/plus-a7.so "$out/core/snes9x2005_plus_libretro.so" \
 build/plus-a7-out/ff6.sfc build/magitek-bio-private/scene.state 1200 > "$out/equivalence-general.log"
python3 build/qualify-a7-pair.py
