#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=build/multigame-fixes-private-v1
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
if test "${1:-}" != --explorer; then
for label in core reference; do
(cd "$out/$label"; make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 CC="arm-linux-gnueabihf-gcc $flags" SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1') > "$out/$label-build.log" 2>&1
done
fi
arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU -std=gnu99 -O2 -Wall -Wextra -Werror -Wno-misleading-indentation -no-pie -nostdlib -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o build/explore-multigame.c -Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o "$out/explore"
echo 'Built isolated HDMA fix and explorer'
