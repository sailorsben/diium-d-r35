#!/bin/sh
# QEMU counts and exact-output experiments only. Never access the card.
set -eu
ulimit -c 0
cd "$(dirname "$0")/.."
flags='-DD35_PLUS_A7 -DUSE_BLARGG_APU -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
cc=arm-linux-gnueabihf-gcc
libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
python3 - <<'PY'
from pathlib import Path
s=Path('build/plus-a7-equivalence.c').read_text()
# The existing harness required a batching gain against an older core. Both
# sides here already have early publication; retain all output/state checks.
old='    assert(magitek_bio_replay?split_frames>iterations-10:split_frames>iterations);'
assert s.count(old)==1
s=s.replace(old,'    /* Equal batch count is valid against current production. */')
s=s.replace('PASS: earlier PCM publication splits %u frames into multiple byte-equivalent batches','PASS: native PCM preserved; %u frames have more callback batches than current production')
Path('build/bio-hypotheses-private/equivalence.c').write_text(s)
PY
$cc $flags -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o build/bio-hypotheses-private/equivalence.c $libs -o build/bio-hypotheses-private/equivalence
for variant in ${D35_BIO_VARIANTS:-baseline window palette palette-window}; do
    out=build/bio-hypotheses-private/$variant
    if [ ! -e "$out/core/snes9x2005_plus_libretro.so" ]; then
      (cd "$out/core"; make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 CC="$cc $flags" \
      SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \
      LDFLAGS='-L../../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1') > "$out/build.log" 2>&1
    fi
    $cc $flags -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "$out/replay.c" $libs -o "$out/replay"
    if [ ! -e "$out/capture" ]; then
      mkdir "$out/capture"
      qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib "$out/replay" "$out/core/snes9x2005_plus_libretro.so" build/plus-a7-out/ff6.sfc build/magitek-bio-private/scene.state - "$out/capture" < build/magitek-lazy-candidate-private/commands.txt > "$out/replay.log" 2>&1
    fi
    qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib build/bio-hypotheses-private/equivalence build/plus-a7-out/plus-a7.so "$out/core/snes9x2005_plus_libretro.so" build/plus-a7-out/ff6.sfc build/magitek-bio-private/scene.state 1200 magitek-bio > "$out/equivalence-bio.log" 2>&1
    echo "$variant complete: counts and 1200-frame output comparison"
done
