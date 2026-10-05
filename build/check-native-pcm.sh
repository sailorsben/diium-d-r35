#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
for check in native-pcm audio-owner; do
  arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
    /usr/arm-linux-gnueabihf/lib/crt1.o "build/snes-mvp/$check-check.c" \
    -Lbuild/sysroot/lib -Wl,--no-as-needed -l:libpthread-2.30.so -l:libc-2.30.so \
    -l:libgcc_s.so.1 -l:ld-2.30.so -o "build/snes-mvp/out/$check-check"
  timeout 12 qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib \
    "build/snes-mvp/out/$check-check" > "build/snes-mvp/out/$check-check.log" 2>&1
  cat "build/snes-mvp/out/$check-check.log"
done
