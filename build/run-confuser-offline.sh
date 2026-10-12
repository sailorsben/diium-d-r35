#!/bin/sh
# Counts and output checks only; QEMU elapsed times are not A7 prices.
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
flags='-DD35_PLUS_A7 -DUSE_BLARGG_APU -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
cc=arm-linux-gnueabihf-gcc
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
for name in ${D35_CONF_VARIANTS:-baseline bg3-window}; do
 out=build/confuser-private-v1/$name
 if [ ! -e "$out/core/snes9x2005_plus_libretro.so" ]; then
  (cd "$out/core"; make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 CC="$cc $flags" \
   SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
   LDFLAGS='-L../../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1') > "$out/build.log" 2>&1
 fi
 $cc $flags -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "$out/replay.c" $libs -o "$out/replay"
 capture="$out/${D35_CONF_REPLAY:-confuser}"
 test ! -e "$capture"
 mkdir "$capture"
 qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib "$out/replay" "$out/core/snes9x2005_plus_libretro.so" build/plus-a7-out/ff6.sfc build/confuser-private-v1/confuser-selection/scene.state - "$capture" < build/confuser-private-v1/cast-input.txt > "$capture/replay.log" 2>&1
 echo "$name work replay complete"
done
