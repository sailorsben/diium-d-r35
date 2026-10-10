#!/bin/sh
# Compare the preserved 1.18 instrumented core with the current isolated copy.
# Both execute the same owner-supplied private scene/menu inputs; no card access.
set -eu
cd "$(dirname "$0")"
test ! -e render-census-bio-lazy
test ! -e magitek-lazy-baseline-private
test ! -e magitek-lazy-candidate-private
python3 prepare-render-census.py render-census-bio-lazy
sh check-render-census.sh render-census-bio-lazy
mkdir magitek-lazy-baseline-private magitek-lazy-candidate-private
sh replay-snes-scene.sh render-census-bio-cache/core/snes9x2005_plus_libretro.so \
 plus-a7-out/ff6.sfc magitek-bio-private/scene.state - magitek-lazy-baseline-private \
 < magitek-cache-census-private/commands.txt > magitek-lazy-baseline-private/replay.log
sh replay-snes-scene.sh render-census-bio-lazy/core/snes9x2005_plus_libretro.so \
 plus-a7-out/ff6.sfc magitek-bio-private/scene.state - magitek-lazy-candidate-private \
 < magitek-cache-census-private/commands.txt > magitek-lazy-candidate-private/replay.log
python3 analyze-color-row-census.py
