#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p snes-mvp/out
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 snes-mvp/main.c snes-mvp/board.c snes-mvp/runner.c snes-mvp/audio-pipe.c snes-mvp/ui.c snes-mvp/startup.c snes-mvp/platform.c snes-mvp/timing.c glibc230-stat-compat.c \
 -L./sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 \
 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so \
 -o snes-mvp/out/snes-mvp
arm-linux-gnueabihf-readelf -V snes-mvp/out/snes-mvp > snes-mvp/out/abi-versions.txt
arm-linux-gnueabihf-readelf -d snes-mvp/out/snes-mvp > snes-mvp/out/dependencies.txt
arm-linux-gnueabihf-size snes-mvp/out/snes-mvp
