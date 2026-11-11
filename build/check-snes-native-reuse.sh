#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=$(realpath "$1")
rt="$out/runner"
check_source=${2:-build/check-snes-native-reuse.c}
flags='-DD35_PLUS_A7 -DD35_NATIVE_PCM -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O3 -ffunction-sections -fdata-sections \
    -Wall -Wextra -Werror -Wno-misleading-indentation -no-pie -nostdlib -Wl,--gc-sections \
    -I"$rt" -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
    "$check_source" "$rt/timing.c" "$rt/native-pcm.c" $libs -o "$out/display-check"
qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib "$out/display-check"
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O3 -flto=4 -Wall -Wextra -Werror \
    -Wno-misleading-indentation -no-pie -nostdlib -Ibuild -Ibuild/snes9x2005/libretro-common/include \
    /usr/arm-linux-gnueabihf/lib/crt1.o "$out/main.c" "$rt/board.c" "$rt/runner.c" "$rt/audio-owner.c" \
    "$rt/native-pcm.c" "$rt/startup.c" "$rt/platform.c" "$rt/timing.c" "$rt/ui.c" build/glibc230-stat-compat.c \
    $libs -o "$out/candidate"
