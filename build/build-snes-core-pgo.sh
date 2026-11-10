#!/bin/sh
# Profile the measured combined source in the ARM replay, then relink it.
set -eu
cd "$(dirname "$0")/.."
repo=$PWD
out=$(realpath "$1")
test ! -e "$out"
mkdir -p "$out/core" "$out/profile" "$out/training-libs"
ln -s "$repo/build/sysroot" "$out/sysroot"
ln -s "$repo/build/sysroot/lib/libz.so.1" "$out/training-libs/libz.so.1"
core="$out/core"
src=build/multigame-fixes-private-v1/core
fixtures="$repo/build/fivegame-kernel-private-v2/cases"
replay=$(realpath "$2")
cp -r "$src/source" "$src/libretro-common" "$src/jni" "$src"/*.c "$src"/*.h "$src"/Makefile* "$src/link.T" "$src/copyright" "$core/"
python3 build/prepare-snes-superfx.py "$core" fx-batch
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
shared='-shared -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T'
libs='-L../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
build() {
    (
        cd "$core"
        make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 GIT_VERSION=' 6b74dc0' \
          CC="arm-linux-gnueabihf-gcc $flags $1 -fprofile-dir=$out/profile" SHARED="$shared $2" LDFLAGS="$3"
    )
}
build -fprofile-generate '' '-lgcov' >"$out/generate.log" 2>&1
for game in 000 001 003; do
    cold=0
    if [ "$game" = 003 ]; then cold=8656; fi
    qemu-arm -cpu cortex-a7 -L /usr/arm-linux-gnueabihf -E "LD_LIBRARY_PATH=$out/training-libs" \
        "$replay" "$core/snes9x2005_plus_libretro.so" "$fixtures/$game" "$cold" cold-off verify \
        >"$out/train-$game.log" 2>&1
done
test -n "$(find "$out/profile" -name '*.gcda' -print -quit)"
mv "$core/snes9x2005_plus_libretro.so" "$out/training.so"
build '-fprofile-use -fprofile-correction -Werror=missing-profile -Werror=coverage-mismatch' -nostdlib "$libs" >"$out/use.log" 2>&1
sha256sum "$core/snes9x2005_plus_libretro.so"
