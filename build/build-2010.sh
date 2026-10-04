#!/bin/sh
set -eu
cd "$(dirname "$0")"
base=$(pwd)
mkdir -p comparison-2010
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -fPIC -c glibc230-stat-compat.c -o comparison-2010/glibc230-stat-compat.o
cd snes9x2010
git rev-parse HEAD > ../comparison-2010/core-source-commit.txt
make -j4 platform=unix HAVE_THREADS=0 \
 CC="arm-linux-gnueabihf-gcc $flags" \
 SHARED='-shared -nostdlib -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=libretro/link.T' \
 LDFLAGS='../comparison-2010/glibc230-stat-compat.o -L../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
cp snes9x2010_libretro.so ../comparison-2010/emu_sfc_2010.so
cd "$base"
arm-linux-gnueabihf-gcc $flags -std=c99 -O2 -Wall -Wextra -fPIC -shared -nostdlib \
 -Wl,--no-undefined -Wl,-Bsymbolic-functions -I./snes9x2005/libretro-common/include \
 emu_sfc_2010.c -L./sysroot/lib -Wl,--no-as-needed \
 -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o comparison-2010/emu_sfc.so
for program in harness adapter-check video-contract-check; do
  source="$program-2010.c"
  dependencies='-l:libdl-2.30.so -l:libz.so.1 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
  if [ "$program" = harness ]; then dependencies="-l:emu_sfc.so $dependencies"; fi
  arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -no-pie -nostdlib \
   -I./snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
   "$source" -L./comparison-2010 -L./sysroot/lib -Wl,--no-as-needed \
   $dependencies -o "comparison-2010/$program-arm"
done
arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o stat-compat-check.c comparison-2010/glibc230-stat-compat.o \
 -L./sysroot/lib -Wl,--no-as-needed -l:libc-2.30.so -l:libgcc_s.so.1 -o comparison-2010/stat-compat-check-arm
arm-linux-gnueabihf-readelf -V comparison-2010/emu_sfc.so comparison-2010/emu_sfc_2010.so comparison-2010/harness-arm > comparison-2010/abi-versions.txt
arm-linux-gnueabihf-readelf -d comparison-2010/emu_sfc.so comparison-2010/emu_sfc_2010.so > comparison-2010/dependencies.txt
