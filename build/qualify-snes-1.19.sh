#!/bin/sh
# Local-only qualification. Private ROM/state inputs and dependency binaries
# stay in ignored build trees; this script never accesses the handheld/card.
set -eu
cd "$(dirname "$0")"
sh build-snes-mvp.sh
python3 prepare-plus-inputs.py --rom plus-a7-out/ff6.sfc --snapshot plus-a7-out/returned.state
sh check-plus-a7.sh
python3 check-color-cache-contract.py
sh check-snes-mvp.sh
sh check-native-pcm.sh
sh check-native-runner.sh
sh check-magitek-bio.sh magitek-bio-private/scene.state
qemu-arm -cpu cortex-a7 -L ./sysroot -E LD_LIBRARY_PATH=./sysroot/lib \
 plus-a7-out/equivalence clean/emu_sfc_plus.so plus-a7-out/plus-a7.so \
 plus-a7-out/ff6.sfc plus-a7-out/returned.state 6000 > plus-a7-out/narshe-long-equivalence.log
tail -n 3 plus-a7-out/narshe-long-equivalence.log
python3 verify-snes-mvp.py > snes-mvp/out/qualification-1.19.log
printf 'PASS: SNES1.19 local qualification; physical performance and audio pending\n'
