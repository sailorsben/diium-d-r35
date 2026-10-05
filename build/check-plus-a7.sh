#!/bin/sh
set -eu
cd "$(dirname "$0")"
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
sha256sum plus-a7-out/plus-a7.so plus-a7-render.h plus-a7-out/returned.state > plus-a7-out/checked-inputs.sha256
arm-linux-gnueabihf-gcc $flags -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o plus-a7-check.c \
 -L./sysroot/lib -Wl,--no-as-needed -l:libc-2.30.so -l:libgcc_s.so.1 -o plus-a7-out/kernel-check
qemu-arm -cpu cortex-a7 -L ./sysroot -E LD_LIBRARY_PATH=./sysroot/lib \
 plus-a7-out/kernel-check > plus-a7-out/kernel-check.log
cat plus-a7-out/kernel-check.log
arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o plus-a7-equivalence.c \
 -L./sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 \
 -o plus-a7-out/equivalence
qemu-arm -cpu cortex-a7 -L ./sysroot -E LD_LIBRARY_PATH=./sysroot/lib plus-a7-out/equivalence \
 ./clean/emu_sfc_plus.so ./plus-a7-out/plus-a7.so ./plus-a7-out/ff6.sfc ./plus-a7-out/returned.state \
 > plus-a7-out/equivalence.log
cat plus-a7-out/equivalence.log
sha256sum -c plus-a7-out/checked-inputs.sha256
arm-linux-gnueabihf-gcc $flags -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 snes-mvp/runner-integration-check.c glibc230-stat-compat.c \
 -L./sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libpthread-2.30.so -l:libz.so.1 \
 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so -o plus-a7-out/runner-integration
qemu-arm -cpu cortex-a7 -L ./sysroot -E LD_LIBRARY_PATH=./sysroot/lib plus-a7-out/runner-integration \
 ./ff3.zip ./plus-a7-out/plus-a7.so ./plus-a7-out/integration-saves > plus-a7-out/runner-integration.log
cat plus-a7-out/runner-integration.log
