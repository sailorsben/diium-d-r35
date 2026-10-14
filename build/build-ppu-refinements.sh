#!/bin/sh
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
out=build/ppu-refinements-private-v4
test ! -e "$out/built.json"
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
for label in obj obj-counted shapes shapes-counted bulk bulk-counted combined combined-counted; do
 extra='';case "$label" in *-counted) extra='-DD35_DEMAND_COUNT -DD35_FUSED_COUNT';;esac
 (cd "$out/$label";make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \
  CC="arm-linux-gnueabihf-gcc $flags $extra" \
  SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
  LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1') > "$out/$label-build.log" 2>&1
 echo "Built PPU $label"
done
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so'
arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild -I"$out" -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "$out/compare.c" $libs -o "$out/compare"
python3 -c 'from pathlib import Path;import hashlib,json;p=Path("build/ppu-refinements-private-v4");(p/"built.json").write_text(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.glob("*/snes9x2005_plus_libretro.so")},indent=2)+"\n")'
