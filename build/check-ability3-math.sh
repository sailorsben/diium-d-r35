#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=build/ability3-private-v1
arm-linux-gnueabihf-gcc -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -DUSE_BLARGG_APU -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o build/plus-a7-math-check.c \
 -Lbuild/sysroot/lib -Wl,--no-as-needed -l:libc-2.30.so -l:libm-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so -o "$out/math-check"
LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot "$out/math-check" > "$out/math-check.log" 2>&1
cat "$out/math-check.log"
