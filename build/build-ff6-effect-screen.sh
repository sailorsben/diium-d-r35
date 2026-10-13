#!/bin/sh
# Offline correctness/work screening; elapsed QEMU time is not A7 evidence.
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
out=build/ff6-effect-screen-private-v1
flags='-DD35_PLUS_A7 -DUSE_BLARGG_APU -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
test -f "$out/prepared.json"
if [ ! -e "$out/core/snes9x2005_plus_libretro.so" ]; then
 (cd "$out/core"; make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \
  CC="arm-linux-gnueabihf-gcc $flags" \
  SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
  LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1') > "$out/core-build.log" 2>&1
fi
test ! -e "$out/screen"
arm-linux-gnueabihf-gcc $flags -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "$out/screen.c" \
 -Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -o "$out/screen"
echo 'Offline effect screen built'
