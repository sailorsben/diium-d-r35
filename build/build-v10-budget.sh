#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p v10-budget
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=c99 -O2 -Wall -Wextra -Werror -fPIC -shared -nostdlib \
 -Wl,--no-undefined -Wl,-Bsymbolic-functions -I./snes9x2005/libretro-common/include \
 emu_sfc_plus_v10_budget.c -L./sysroot/lib -Wl,--no-as-needed \
 -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o v10-budget/emu_sfc.so
arm-linux-gnueabihf-readelf -V v10-budget/emu_sfc.so > v10-budget/abi-versions.txt
arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 v10-budget-check.c -L./sysroot/lib -Wl,--no-as-needed \
 -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o v10-budget/check-arm
