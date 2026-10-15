#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o build/uart-state-owner.c \
 -Lbuild/sysroot/lib -Wl,--no-as-needed -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so \
 -o build/uart-kernel-private/uart-state-owner
arm-linux-gnueabihf-readelf -V build/uart-kernel-private/uart-state-owner > build/uart-kernel-private/owner-abi.txt
