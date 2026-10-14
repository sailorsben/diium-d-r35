#!/bin/sh
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
out=build/demand-final-private-v2
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
prefix=transition
if test "${1:-}" = --deterministic; then prefix=transition-fixed; fi
for label in "$prefix-reference" "$prefix-candidate"; do
 if test -e "$out/$label/snes9x2005_plus_libretro.so"; then continue; fi
 extra='';if test "$label" = "$prefix-candidate"; then extra='-DD35_DEMAND_COUNT'; fi
 (cd "$out/$label";make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \
 CC="arm-linux-gnueabihf-gcc $flags $extra" \
 SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
 LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1') > "$out/$label-build.log" 2>&1
 echo "Built $label"
done
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so'
arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild -I"$out" -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "$out/$prefix-compare.c" $libs -o "$out/$prefix-compare"
python3 build/qualify-demand-transitions.py "${1:-}"
