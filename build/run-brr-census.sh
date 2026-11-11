#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
repo=$PWD
out=/tmp/d35-brr-census-20261111
test ! -e "$out"
mkdir -p "$out"
cp -a /home/sailorsben/d35-audit-bounded-01/core "$out/core"
ln -s "$repo/build/sysroot" "$out/sysroot"
python3 build/prepare-brr-census.py "$out/core"
cd "$out/core"
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
make -j6 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 GIT_VERSION=' 6b74dc0' CC="arm-linux-gnueabihf-gcc $flags" SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' LDFLAGS='-L../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1' >"$out/build.log" 2>&1
cd "$repo"
for id in 000 001 002 003 004; do
  cold=0; mode=full
  if [ "$id" = 003 ]; then cold=8656; mode=cold-off; fi
  (qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib -E D35_BRR_CENSUS_SKIP="$cold" /home/sailorsben/d35-audit-bounded-01/replay "$out/core/snes9x2005_plus_libretro.so" "build/fivegame-kernel-private-v2/cases/$id" "$cold" "$mode" verify >"$out/$id.log" 2>&1; tail -3 "$out/$id.log") &
done
wait
