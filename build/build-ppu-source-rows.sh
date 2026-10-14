#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=build/ppu-refinements-private-v4
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
for label in rows-v2 rows-v2-counted; do
 test ! -e "$out/$label/snes9x2005_plus_libretro.so"
 extra='';if test "$label" = rows-v2-counted;then extra='-DD35_DEMAND_COUNT -DD35_FUSED_COUNT';fi
 (cd "$out/$label";make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 CC="arm-linux-gnueabihf-gcc $flags $extra" \
 SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
 LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1') > "$out/$label-build.log" 2>&1
 echo "Built isolated PPU $label"
done
