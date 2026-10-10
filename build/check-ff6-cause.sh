#!/bin/sh
set -eu
cd "$(dirname "$0")"
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
cd ff6-cause-private/core
make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \
 CC="arm-linux-gnueabihf-gcc $flags" \
 SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
 LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1' \
 > ../build.log 2>&1
cd ../..
mkdir ff6-cause-private/replay
sh replay-snes-scene.sh ff6-cause-private/core/snes9x2005_plus_libretro.so \
 plus-a7-out/ff6.sfc magitek-bio-private/scene.state - ff6-cause-private/replay \
 < magitek-cache-census-private/commands.txt > ff6-cause-private/replay/trace.log
