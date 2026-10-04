#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p v5-capture
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=c99 -O2 -Wall -Wextra -fPIC -shared -nostdlib \
 -Wl,--no-undefined -Wl,-Bsymbolic-functions -I./snes9x2005/libretro-common/include \
 emu_sfc_plus_v5_capture.c -L./sysroot/lib -Wl,--no-as-needed \
 -l:libpthread-2.30.so -l:ld-2.30.so -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o v5-capture/emu_sfc.so
cp emu_sfc_plus.so v5-capture/emu_sfc_plus.so
arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -no-pie -nostdlib \
 -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 harness-v5-capture.c -L./v5-capture -L./sysroot/lib -Wl,--no-as-needed \
 -l:emu_sfc.so -l:libpthread-2.30.so -l:ld-2.30.so -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o v5-capture/harness-arm
arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -no-pie -nostdlib \
 -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 adapter-check-v5-capture.c -L./sysroot/lib -Wl,--no-as-needed \
 -l:libpthread-2.30.so -l:ld-2.30.so -l:libdl-2.30.so -l:libz.so.1 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -o v5-capture/adapter-check-arm
arm-linux-gnueabihf-readelf -V v5-capture/emu_sfc.so v5-capture/emu_sfc_plus.so v5-capture/harness-arm > v5-capture/abi-versions.txt
arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -no-pie -nostdlib \
 -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 video-contract-check-v5-capture.c -L./sysroot/lib -Wl,--no-as-needed \
 -l:libpthread-2.30.so -l:ld-2.30.so -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o v5-capture/video-contract-check-arm
arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o audio-diagnostics-check-v5.c -L./sysroot/lib -Wl,--no-as-needed \
 -l:libpthread-2.30.so -l:ld-2.30.so -l:libdl-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -o v5-capture/audio-diagnostics-check-arm
