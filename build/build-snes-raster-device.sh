#!/bin/sh
# Build only the card diagnostic. All core artifacts were qualified separately.
set -eu
out=$(realpath -m "$1")
test ! -e "$out"
cd "$(dirname "$0")/.."
mkdir -p "$out"
arm-linux-gnueabihf-gcc -std=gnu11 -O2 -DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 \
    -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32 \
    -Wall -Wextra -Werror -no-pie -nostdlib -Ibuild/snes9x2005/libretro-common/include \
    /usr/arm-linux-gnueabihf/lib/crt1.o build/snes-throughput-pair.c -Lbuild/sysroot/lib \
    -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 \
    -o "$out/pair"
arm-linux-gnueabihf-readelf -V "$out/pair" > "$out/abi.txt"
cp build/snes-raster-device-launch.sh "$out/launch.sh"
