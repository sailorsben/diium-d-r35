#!/bin/sh
# Local inspection only. Capture artifacts contain private game pixels/PCM.
set -eu
if [ "$#" -ne 5 ]; then
  printf 'Usage: %s core.so rom.sfc snapshot.state existing-output-directory frames\n' "$0" >&2
  exit 2
fi
BASE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
test -d "$4"
arm-linux-gnueabihf-gcc -DUSE_BLARGG_APU -std=gnu99 -mcpu=cortex-a7 -mfpu=neon-vfpv4 \
 -mfloat-abi=hard -marm -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I"$BASE/snes9x2005/libretro-common/include" /usr/arm-linux-gnueabihf/lib/crt1.o \
 "$BASE/capture-snes-scene.c" -L"$BASE/sysroot/lib" -Wl,--no-as-needed \
 -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 \
 -o "$BASE/plus-a7-out/capture-scene"
qemu-arm -cpu cortex-a7 -L "$BASE/sysroot" -E LD_LIBRARY_PATH="$BASE/sysroot/lib" \
 "$BASE/plus-a7-out/capture-scene" "$@"
