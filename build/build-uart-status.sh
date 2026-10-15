#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
task_root=$(pwd)
cache=${D35_UART_KERNEL_CACHE:-$HOME/.cache/d35-uart-kernel}
kernel=$cache/source
private=$task_root/build/uart-status-private
test -f "$kernel/include/generated/autoconf.h"
test -f "$private/uart-status-guards.h"
export PATH="$cache/hosttools/root/usr/bin:$PATH"
export M4="$cache/hosttools/root/usr/bin/m4"
export BISON_PKGDATADIR="$cache/hosttools/root/usr/share/bison"
mkdir -p "$cache/status"
cp "$task_root/build/uart-status-observer.c" "$cache/status/d35_uart_status.c"
cp "$private/uart-status-guards.h" "$cache/status/"
cp "$private/Module.symvers" "$kernel/Module.symvers"
printf 'obj-m := d35_uart_status.o\nccflags-y := -march=armv7-a -marm\n' > "$cache/status/Makefile"
make -C "$kernel" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- M="$cache/status" modules > "$private/build.log" 2>&1
cp "$cache/status/d35_uart_status.ko" "$private/"
cp "$kernel/.config" "$private/reconstructed.config"
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
arm-linux-gnueabihf-gcc $flags -std=gnu99 -O2 -Wall -Wextra -Werror -no-pie -nostdlib \
 /usr/arm-linux-gnueabihf/lib/crt1.o build/uart-status-owner.c \
 -Lbuild/sysroot/lib -Wl,--no-as-needed -l:libc-2.30.so -l:libgcc_s.so.1 -l:ld-2.30.so \
 -o "$private/uart-status-owner"
