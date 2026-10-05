#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p platform-lab-out
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o platform-lab.c snes-mvp/board.c \
 snes-mvp/ui.c snes-mvp/startup.c snes-mvp/platform.c snes-mvp/timing.c \
 -L./sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libpthread-2.30.so \
 -l:librt-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so \
 -o platform-lab-out/platform-lab
arm-linux-gnueabihf-readelf -V platform-lab-out/platform-lab > platform-lab-out/abi.txt
arm-linux-gnueabihf-objdump -d platform-lab-out/platform-lab > platform-lab-out/disassembly.txt
arm-linux-gnueabihf-size platform-lab-out/platform-lab
