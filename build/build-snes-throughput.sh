#!/bin/sh
# Build in a fresh WSL/Linux scratch directory, separate from the card and packages.
set -eu
test "$#" -ge 1
cd "$(dirname "$0")/.."
repo=$PWD
out=$(realpath "$1")
shift
test "$#" -gt 0 || set -- baseline counter dispatch census
test ! -e "$out"
mkdir "$out"
src=build/multigame-fixes-private-v1/core
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
ln -s "$repo/build/sysroot" "$out/sysroot"
arm-linux-gnueabihf-gcc -std=gnu11 -O2 $flags \
  -marm -Wall -Wextra -Werror -no-pie -nostdlib -Ibuild/snes9x2005/libretro-common/include \
  /usr/arm-linux-gnueabihf/lib/crt1.o build/snes-throughput-replay.c -Lbuild/sysroot/lib \
  -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o "$out/replay"
for mode do
    case $mode in
        apu-*) prepare=build/prepare-snes-scheduler.py ;;
        raster-*) prepare=build/prepare-snes-raster.py ;;
        baseline|counter|dispatch|census|hot|dma-same|dma-delta|dma-census|reuse-census|span-census|offset-row|offset-census|offset-plain|offset-plain-census) prepare=build/prepare-snes-throughput.py ;;
        *) exit 2 ;;
    esac
    mkdir "$out/$mode"
    cp -r "$src/source" "$src/libretro-common" "$src/jni" "$src"/*.c "$src"/*.h "$src"/Makefile* "$src/link.T" "$src/copyright" "$out/$mode/"
    python3 "$prepare" "$out/$mode" "$mode"
done
build_one() {
    mode=$1
    (
        cd "$out/$mode"
        make -B -j3 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 GIT_VERSION=' 6b74dc0' \
          CC="arm-linux-gnueabihf-gcc $flags" \
          SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
          LDFLAGS='-L../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
    ) >"$out/$mode-build.log" 2>&1
    sha256sum "$out/$mode/snes9x2005_plus_libretro.so"
}
pids=''
for mode do
    build_one "$mode" &
    pids="$pids $!"
done
failed=0
for pid in $pids; do wait "$pid" || failed=1; done
test "$failed" -eq 0
