#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -e build/ff6-ability-lab-private-v1/scene.state ]; then
 python3 build/prepare-ff6-ability-lab.py bootstrap
fi
if [ ! -e build/ff6-ability-lab-private-v1/prepared.json ]; then
 python3 build/prepare-ff6-ability-lab.py
fi
if [ ! -e build/ff6-ability-lab-private-v1/ready.json ]; then
 python3 build/prepare-ff6-ability-lab.py finalize
fi
test ! -e build/ff6-ability-lab-private-v1/check
arm-linux-gnueabihf-gcc -DUSE_BLARGG_APU -std=gnu99 -mcpu=cortex-a7 -mfpu=neon-vfpv4 \
 -mfloat-abi=hard -marm -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
 build/ff6-ability-lab-check.c -Lbuild/sysroot/lib -Wl,--no-as-needed \
 -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 \
 -o build/ff6-ability-lab-private-v1/check
