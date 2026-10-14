#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=build/fused-toolbox-private-v1
if [ "${1:-}" = '--v2' ]; then out=build/fused-toolbox-private-v2; elif [ "$#" != 0 ]; then exit 2; fi
for name in d35_fused_band_0_0 d35_fused_band_0_1 d35_fused_band_1_0 d35_fused_band_3_0; do
 arm-linux-gnueabihf-objdump -d --disassemble=$name "$out/plus-a7.so" > "$out/asm-$name.txt"
done
arm-linux-gnueabihf-readelf -V "$out/plus-a7.so" > "$out/abi.txt"
