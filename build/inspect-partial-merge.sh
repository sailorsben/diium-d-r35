#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=build/partial-candidates-private-v1
for variant in local sparse; do
 for mode in 0 1 3; do
  arm-linux-gnueabihf-objdump -d --disassemble=d35_band_$mode "$out/$variant/snes9x2005_plus_libretro.so" > "$out/asm-$variant-$mode.txt"
 done
done
for name in mask_old mask_new; do
 arm-linux-gnueabihf-objdump -d --disassemble=$name "$out/kernel-check" > "$out/asm-$name.txt"
done
out=build/partial-selective-private-v1
for mode in 0 1 3; do
 arm-linux-gnueabihf-objdump -d --disassemble=d35_band_$mode "$out/selective/snes9x2005_plus_libretro.so" > "$out/asm-selective-$mode.txt"
done
