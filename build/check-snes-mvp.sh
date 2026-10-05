#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
base=$(pwd)
out="$base/build/snes-mvp/out"
mkdir -p "$out/smoke-final" "$out/preview" "$out/contracts"
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I"$base/build/snes9x2005/libretro-common/include" /usr/arm-linux-gnueabihf/lib/crt1.o \
 "$base/build/snes-mvp/runner-check.c" "$base/build/glibc230-stat-compat.c" \
 -L"$base/build/sysroot/lib" -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 \
 -l:libpthread-2.30.so -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so \
 -o "$out/runner-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/runner-check-arm" "$out/contracts" > "$out/contracts.log"
D35_MVP_FRAMES=180 D35_MVP_NO_PACING=1 \
 qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/snes-mvp" --mock --rom "$base/build/ff3.zip" --core "$base/build/plus-a7-out/plus-a7.so" \
 --saves "$out/smoke-final" > "$out/smoke.log" 2>&1
D35_MVP_FRAMES=30 timeout 8 \
 qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/snes-mvp" --mock --rom "$base/build/ff3.zip" --core "$base/build/plus-a7-out/plus-a7.so" \
 --saves "$out/paced-smoke" > "$out/paced-smoke.log" 2>&1
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/snes-mvp" --preview "$out/preview"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/snes-mvp" --list --romdir "$base/build" > "$out/library-list.txt"
if qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/snes-mvp" --mock --rom "$base/build/snes-mvp/ui.h" --core "$base/build/clean/emu_sfc_plus.so" \
 --saves "$out/reject" > "$out/reject.log" 2>&1; then
 echo 'Invalid ROM was accepted' >&2
 exit 1
fi
cat "$out/contracts.log"
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I"$base/build/snes9x2005/libretro-common/include" /usr/arm-linux-gnueabihf/lib/crt1.o \
 "$base/build/snes-mvp/startup-check.c" "$base/build/snes-mvp/ui.c" \
 "$base/build/snes-mvp/startup.c" "$base/build/snes-mvp/timing.c" "$base/build/glibc230-stat-compat.c" \
 -L"$base/build/sysroot/lib" -Wl,--no-as-needed -l:libpthread-2.30.so \
 -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so -o "$out/startup-check-arm"
mkdir -p "$out/startup-contract"
rm -f "$out/startup-contract/ready" "$out/startup-contract/startup.log"
timeout 10 qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" \
 -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 -E D35_MVP_STARTUP_LOG="$out/startup-contract/startup.log" \
 -E D35_MVP_READY_FILE="$out/startup-contract/ready" \
 "$out/startup-check-arm" "$out/startup-contract" > "$out/startup-contract.log"
test -f "$out/startup-contract/ready"
cat "$out/startup-contract.log"
python3 "$base/build/snes-mvp/extract-vendor-input.py" "$base/build/launcher-clock/vrtemu.original" \
 "$out/vendor-input-reference.h" > "$out/vendor-input-reference.log"
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -I"$base/build/snes9x2005/libretro-common/include" -I"$out" /usr/arm-linux-gnueabihf/lib/crt1.o \
 "$base/build/snes-mvp/board-input-check.c" "$base/build/snes-mvp/timing.c" \
 -L"$base/build/sysroot/lib" -Wl,--no-as-needed -l:libdl-2.30.so -l:libpthread-2.30.so \
 -l:librt-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so -o "$out/board-input-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/board-input-check-arm" > "$out/board-input-contract.log"
cat "$out/board-input-contract.log"
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o "$base/build/snes-mvp/platform-check.c" "$base/build/snes-mvp/timing.c" \
 -L"$base/build/sysroot/lib" -Wl,--no-as-needed -l:libc-2.30.so -l:libgcc_s.so.1 -o "$out/platform-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/platform-check-arm" > "$out/platform-contract.log"
cat "$out/platform-contract.log"
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o "$base/build/snes-mvp/timing-check.c" \
 -L"$base/build/sysroot/lib" -Wl,--no-as-needed -l:libc-2.30.so -l:libgcc_s.so.1 -o "$out/timing-check-arm"
qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/timing-check-arm" > "$out/timing-contract.log"
timeout 5 qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/timing-check-arm" --real >> "$out/timing-contract.log"
cat "$out/timing-contract.log"
python3 "$base/build/snes-mvp/check-startup-wrapper.py" "$out/wrapper-contract" > "$out/wrapper-contract.log"
cat "$out/wrapper-contract.log"
printf 'PASS: final ARM binary, exact core ZIP smoke, UI preview, library scan and invalid ROM rejection\n'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o "$base/build/snes-mvp/display-queue-check.c" "$base/build/snes-mvp/timing.c" \
 -L"$base/build/sysroot/lib" -Wl,--no-as-needed -l:libdl-2.30.so -l:libpthread-2.30.so \
 -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so -o "$out/display-queue-check-arm"
timeout 10 qemu-arm -cpu cortex-a7 -L "$base/build/sysroot" -E LD_LIBRARY_PATH="$base/build/sysroot/lib" \
 "$out/display-queue-check-arm" > "$out/display-queue-contract.log"
cat "$out/display-queue-contract.log"
