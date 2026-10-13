#!/bin/sh
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
out=build/fixed-rows-private-v3
flags='-DUSE_BLARGG_APU -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libz.so.1 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
for variant in original candidate; do
 define=''
 if [ "$variant" = candidate ]; then define='-DD35_CLIPPING_CANDIDATE'; fi
 arm-linux-gnueabihf-gcc $flags $define -std=gnu99 -O3 -Wall -Wextra -Werror -Wno-sign-compare -Wno-implicit-fallthrough -no-pie -nostdlib \
  -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
  build/plus-a7-fixed-clipping-check.c $libs -o "$out/clipping-$variant"
 LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot \
  "$out/clipping-$variant" > "$out/clipping-$variant.crc" 2> "$out/clipping-$variant.log"
done
cmp "$out/clipping-original.crc" "$out/clipping-candidate.crc"
echo 'PASS: actual clipped renderer matches independently flushed original rows' > "$out/clipping-exact.log"
