#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=build/demand-private-v1
rt="$out/runtime-v1"
test ! -e "$out/runtime-proof.json"
gcc -std=gnu99 -O2 -Wall -Wextra -Werror -pthread -I"$rt" "$rt/display-queue-check.c" "$rt/timing.c" -ldl -o "$out/display-queue-check"
"$out/display-queue-check" > "$out/display-queue-check.log"
flags='-DD35_NATIVE_PCM -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so'
arm-linux-gnueabihf-gcc $flags -O3 -flto=4 -std=gnu99 -Wall -Wextra -Werror -Wno-misleading-indentation -no-pie -nostdlib \
 -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 "$rt/main.c" "$rt/ui.c" "$rt/board.c" "$rt/runner.c" "$rt/audio-owner.c" "$rt/native-pcm.c" "$rt/startup.c" "$rt/platform.c" "$rt/timing.c" \
 build/glibc230-stat-compat.c $libs -o "$out/owned-output-runner"
arm-linux-gnueabihf-readelf -V "$out/owned-output-runner" > "$out/runtime-abi.txt"
python3 -c 'from pathlib import Path;import json,hashlib;p=Path("build/demand-private-v1");(p/"runtime-proof.json").write_text(json.dumps({"passed":True,"FIFO_output":(p/"display-queue-check.log").read_text().strip(),"runner_sha256":hashlib.sha256((p/"owned-output-runner").read_bytes()).hexdigest(),"physical_driver_qualified":False},indent=2)+"\n")'
cat "$out/display-queue-check.log"
