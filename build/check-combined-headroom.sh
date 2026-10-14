#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=build/combined-test-private-v1
test ! -e "$out/headroom-check.log"
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libc-2.30.so -l:libgcc_s.so.1'
arm-linux-gnueabihf-gcc -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm \
 -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32 \
 -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib -Ibuild \
 /usr/arm-linux-gnueabihf/lib/crt1.o build/combined-headroom-check.c $libs -o "$out/headroom-check"
LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot \
 "$out/headroom-check" "$out/headroom-fixtures" > "$out/headroom-check.log" 2>&1
