#!/bin/sh
# Build one scratch-only experiment from the pinned optimization stack's source.
set -eu
test "$#" -eq 3
cd "$(dirname "$0")/.."
repo=$PWD
source=$(realpath "$1")
out=$(realpath "$2")
mode=$3
test ! -e "$out"
mkdir -p "$out/core"
ln -s "$repo/build/sysroot" "$out/sysroot"
tar -C "$source" --exclude='*.o' --exclude='*.so' --exclude='*.gcda' --exclude='*.gcno' -cf - . |
    tar -C "$out/core" -xf -
python3 build/prepare-snes-stack-audit.py "$out/core" "$mode"
cd "$out/core"
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
make -j6 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 GIT_VERSION=' 6b74dc0' \
    CC="arm-linux-gnueabihf-gcc $flags" \
    SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
    LDFLAGS='-L../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1' \
    >"$out/build.log" 2>&1
cp snes9x2005_plus_libretro.so "$out/control.so"
cp snes9x2005_plus_libretro.so "$out/candidate.so"
sha256sum "$out/control.so" "$out/candidate.so"
