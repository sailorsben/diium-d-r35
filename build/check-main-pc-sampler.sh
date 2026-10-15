#!/bin/sh
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
out=build/compiler-research-private-v1
gcc -std=gnu99 -O2 -Wall -Wextra -Werror -Wno-misleading-indentation -Ibuild build/check-main-pc-sampler.c -ldl -lrt -pthread -o "$out/pc-check-host3"
"$out/pc-check-host3" "$out/pc-host" > "$out/pc-host3.log"
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -Wno-misleading-indentation -no-pie -nostdlib -Ibuild /usr/arm-linux-gnueabihf/lib/crt1.o build/check-main-pc-sampler.c $libs -o "$out/pc-check-arm"
mkdir -p "$out/pc-arm"
LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot "$out/pc-check-arm" "$out/pc-arm" > "$out/pc-arm.log" 2>&1
