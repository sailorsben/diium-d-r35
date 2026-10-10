#!/bin/sh
# Compare with the unchanged stock-derived implementation, including empty bands.
set -eu
cd "$(dirname "$0")/.."
mkdir -p build/ff6-window-batch-private
gcc -DUSE_BLARGG_APU -std=c99 -O2 -Wall -Wextra -Werror \
 -Wno-error=implicit-fallthrough -Ibuild/snes9x2005/libretro-common/include \
 build/plus-a7-window-check.c -o build/ff6-window-batch-private/window-check
build/ff6-window-batch-private/window-check >build/ff6-window-batch-private/window-check.log
cat build/ff6-window-batch-private/window-check.log
gcc -std=c99 -Wall -Wextra -Werror -fsyntax-only build/ff6-bio-blast.c
for source in build/ff6-cause-private/c-map/bank-*.c; do
 gcc -std=c99 -Wall -Wextra -Werror -fsyntax-only "$source"
done
printf '%s\n' 'PASS: focused readable C and all eight low-level C banks pass syntax checks' \
 >build/ff6-window-batch-private/c-map-syntax.log
