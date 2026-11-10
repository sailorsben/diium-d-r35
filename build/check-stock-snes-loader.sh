#!/bin/sh
set -eu
vendor=$(realpath "$1")
out=$(realpath "$2")
cd "$(dirname "$0")/.."
test "$(sha256sum "$vendor" | cut -d' ' -f1)" = 8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72
mkdir "$out"
arm-linux-gnueabihf-gcc -Wall -Wextra -Werror -std=gnu11 -mcpu=cortex-a7 -marm \
    -O2 -fPIE -pie build/check-stock-snes-loader.c -o "$out/check"
timeout 10 qemu-arm -cpu cortex-a7 -L /usr/arm-linux-gnueabihf "$out/check" "$vendor"
