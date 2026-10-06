#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 apply-plus-a7.py
mkdir -p plus-a7-out
cd snes9x2005
make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \
 CC='arm-linux-gnueabihf-gcc -DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32' \
 SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
 LDFLAGS='-L../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1' \
 > ../plus-a7-out/build.log 2>&1
cp snes9x2005_plus_libretro.so ../plus-a7-out/plus-a7.so
arm-linux-gnueabihf-readelf -V ../plus-a7-out/plus-a7.so > ../plus-a7-out/abi-versions.txt
arm-linux-gnueabihf-objdump -d ../plus-a7-out/plus-a7.so > ../plus-a7-out/disassembly.txt
sha256sum ../plus-a7-out/plus-a7.so
