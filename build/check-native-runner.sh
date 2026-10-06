#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
out=build/snes-mvp/out
mkdir -p "$out/native-lifecycle-saves"
python3 -c 'from pathlib import Path; import json,shutil,zlib; core=Path("build/plus-a7-out/plus-a7.so").read_bytes(); name="game-a27f1c7a-3145728-core-%08x-%d.state"%(zlib.crc32(core)&0xffffffff,len(core)); shutil.copy2(Path("build/plus-a7-out/integration-saves")/name,Path("build/snes-mvp/out/native-lifecycle-saves")/name)'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 build/snes-mvp/native-runner-check.c build/glibc230-stat-compat.c \
 -Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libpthread-2.30.so -l:libz.so.1 \
 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so -o "$out/native-runner-check"
timeout 20 qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib \
 "$out/native-runner-check" build/ff3.zip build/plus-a7-out/plus-a7.so "$out/native-lifecycle-saves" \
 > "$out/native-runner-check.log" 2>&1
cat "$out/native-runner-check.log"
