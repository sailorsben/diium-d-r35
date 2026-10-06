#!/bin/sh
set -eu
cd "$(dirname "$0")"
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
census=${1:-render-census}
case "$census" in render-census*) ;; *) exit 1;; esac
cd "$census/core"
make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \
 CC="arm-linux-gnueabihf-gcc $flags" \
 SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
 LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1' \
 > ../build.log 2>&1
cd ../..
arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I. -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "$census/replay.c" \
 -L./sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 \
 -o "$census/replay"
qemu-arm -cpu cortex-a7 -L ./sysroot -E LD_LIBRARY_PATH=./sysroot/lib "$census/replay" \
 ./clean/emu_sfc_plus.so "./$census/core/snes9x2005_plus_libretro.so" \
 ./plus-a7-out/ff6.sfc ./plus-a7-out/returned.state > "$census/replay.log"
tail -n 3 "$census/replay.log"
