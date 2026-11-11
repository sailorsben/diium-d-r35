#!/bin/sh
set -eu
test "$#" -eq 1
cd "$(dirname "$0")/.."
out=$(realpath "$1")
python3 build/prepare-snes-pcm-audit.py build/stock-shell-display-private-v2 "$out"
flags='-DD35_PLUS_A7 -DD35_NATIVE_PCM -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
    -I"$out/runner" /usr/arm-linux-gnueabihf/lib/crt1.o build/check-snes-pcm-audit.c \
    -Lbuild/sysroot/lib -Wl,--no-as-needed -l:libc-2.30.so -l:libgcc_s.so.1 -o "$out/pcm-check"
qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib "$out/pcm-check"
sh build/check-snes-native-reuse.sh "$out"
