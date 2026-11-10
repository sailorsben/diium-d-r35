#!/bin/sh
# Run the generated kernels and original interpreter on the ARM test target.
set -eu
core=$(realpath "$1")/fx-batch
cd "$(dirname "$0")/.."
out="$core/superfx-check"
arm-linux-gnueabihf-gcc -O3 -mcpu=cortex-a7 -marm -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32 \
    -Wall -Wextra -Werror -Wno-sign-compare -no-pie -nostdlib \
    -I"$core/source" -I"$core/libretro-common/include" /usr/arm-linux-gnueabihf/lib/crt1.o \
    build/check-snes-superfx-batch.c "$core/source/fxemu.c" -Lbuild/sysroot/lib \
    -l:libc-2.30.so -l:libgcc_s.so.1 -o "$out"
qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib "$out"
