#!/bin/sh
# Isolated diagnostic binary; never rebuild or change the qualified 1.19 core.
set -eu
cd "$(dirname "$0")/.."
out=build/snes-focus-out
mkdir -p "$out/contracts" "$out/smoke" "$out/native-saves"
flags='-DD35_FOCUS_PROFILE -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libpthread-2.30.so -l:librt-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so'
python3 -c 'from pathlib import Path;import json,hashlib; m=json.loads(Path("releases/snes-mvp-1.19/manifest.json").read_text());assert hashlib.sha256(Path("build/plus-a7-out/plus-a7.so").read_bytes()).hexdigest()==m["core_sha256"]'
arm-linux-gnueabihf-gcc $flags -DD35_NATIVE_PCM -std=gnu99 -O3 -flto=4 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 build/snes-mvp/main.c build/snes-mvp/board.c build/snes-mvp/runner.c build/snes-mvp/audio-owner.c \
 build/snes-mvp/native-pcm.c build/snes-mvp/ui.c build/snes-mvp/startup.c build/snes-mvp/platform.c \
 build/snes-mvp/timing.c build/glibc230-stat-compat.c $libs -o "$out/snes-mvp"
arm-linux-gnueabihf-readelf -V "$out/snes-mvp" > "$out/abi.txt"
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 build/snes-mvp/focus-profile-check.c build/glibc230-stat-compat.c $libs -o "$out/focus-check"
qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib \
 "$out/focus-check" "$out/contracts" evidence/2026-10-10/snes-mvp-1.19-return/session-failure.txt > "$out/focus-check.log"
cat "$out/focus-check.log"
D35_MVP_FRAMES=180 D35_MVP_NO_PACING=1 qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib \
 "$out/snes-mvp" --mock --rom build/ff3.zip --core build/plus-a7-out/plus-a7.so --saves "$out/smoke" > "$out/smoke.log" 2>&1
python3 -c 'from pathlib import Path;import shutil,zlib; c=Path("build/plus-a7-out/plus-a7.so").read_bytes();n="game-a27f1c7a-3145728-core-%08x-%d.state"%(zlib.crc32(c)&0xffffffff,len(c));shutil.copy2(Path("build/plus-a7-out/integration-saves")/n,Path("build/snes-focus-out/native-saves")/n)'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 build/snes-mvp/native-runner-check.c build/glibc230-stat-compat.c $libs -o "$out/native-check"
timeout 30 qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib \
 "$out/native-check" build/ff3.zip build/plus-a7-out/plus-a7.so "$out/native-saves" > "$out/native-check.log" 2>&1
cat "$out/native-check.log"
python3 build/verify-snes-focus.py
