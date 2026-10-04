#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p hardware-inventory
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=c99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o hardware-inventory.c glibc230-stat-compat.c \
 -L./sysroot/lib -Wl,--no-as-needed -l:libc-2.30.so -l:libgcc_s.so.1 \
 -o hardware-inventory/hardware_probe
arm-linux-gnueabihf-readelf -V hardware-inventory/hardware_probe > hardware-inventory/abi-versions.txt
