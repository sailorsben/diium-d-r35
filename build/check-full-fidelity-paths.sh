#!/bin/sh
# Offline logical/memory checks, never a timing or installation receipt.
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
flags='-DUSE_BLARGG_APU -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O3 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 build/plus-a7-fixed-rows-check.c $libs -o build/fixed-rows-private-v3/row-check
LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot \
 build/fixed-rows-private-v3/row-check > build/fixed-rows-private-v3/row-check.log 2>&1
if [ -e build/subscreen-rows-private-v1/check.c ] && [ ! -e build/subscreen-rows-private-v1/check.log ]; then
 arm-linux-gnueabihf-gcc $flags -std=gnu99 -O3 -Wall -Wextra -Werror -no-pie -nostdlib \
  -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
  build/subscreen-rows-private-v1/check.c $libs -o build/subscreen-rows-private-v1/check
 LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot \
  build/subscreen-rows-private-v1/check > build/subscreen-rows-private-v1/check.log 2>&1
fi
