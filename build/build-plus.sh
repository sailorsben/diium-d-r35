#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
cd sysroot/lib
ln -sf ld-2.30.so ld-linux-armhf.so.3
ln -sf libc-2.30.so libc.so.6
ln -sf libm-2.30.so libm.so.6
ln -sf libdl-2.30.so libdl.so.2
ln -sf libpthread-2.30.so libpthread.so.0
ln -sf librt-2.30.so librt.so.1
cd "$base/snes9x2005"
git rev-parse HEAD > ../core-source-commit.txt
make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \
 CC='arm-linux-gnueabihf-gcc -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32' \
 SHARED='-shared -nostdlib -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
 LDFLAGS='-L../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
