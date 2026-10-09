#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o build/check-stock-boot.c \
 -Wl,-Ttext-segment=0x100000 -Lbuild/sysroot/lib -Wl,--no-as-needed \
 -l:libdl-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so \
 -o build/vesper-boot-private/check-stock-boot
qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib \
 build/vesper-boot-private/check-stock-boot "$1" "$2"
