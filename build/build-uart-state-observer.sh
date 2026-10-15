#!/bin/sh
# Offline only. Uses the checksum-verified upstream 4.19.128 cache prepared for
# this investigation. Builds modules, never a boot image or deployment package.
set -eu
cd "$(dirname "$0")/.."
task_root=$(pwd)
cache=${D35_UART_KERNEL_CACHE:-$HOME/.cache/d35-uart-kernel}
kernel=$cache/source
private=$task_root/build/uart-kernel-private
test -f "$kernel/Makefile"
test -f "$private/uart-state-guards.h"
export PATH="$cache/hosttools/root/usr/bin:$PATH"
export M4="$cache/hosttools/root/usr/bin/m4"
export BISON_PKGDATADIR="$cache/hosttools/root/usr/share/bison"
cd "$kernel"
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- tinyconfig > "$cache/config.log" 2>&1
scripts/config --enable EXPERT --enable MODULES --enable MODULE_UNLOAD \
 --enable KALLSYMS --disable SMP --disable PREEMPT --enable ARCH_MULTI_V7 \
 --enable ARCH_VEXPRESS --enable CPU_V7 --enable MMU --enable SYSFS \
 --enable PROC_FS --enable BINFMT_ELF --enable AEABI --disable MODVERSIONS \
 --disable MODULE_SRCVERSION_ALL --disable FTRACE --disable TRACING \
 --disable DEBUG_INFO --disable MODULE_SIG --disable SECURITY \
 --disable THUMB2_KERNEL --enable UNUSED_SYMBOLS --enable PERF_EVENTS \
 --enable DEBUG_KERNEL --enable FRAME_POINTER --disable ARM_UNWIND \
 --disable ARM_MODULE_PLTS --enable BUG --set-str LOCALVERSION ""
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- olddefconfig >> "$cache/config.log" 2>&1
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- modules_prepare > "$cache/prepare.log" 2>&1
cp "$private/Module.symvers" "$kernel/Module.symvers"
mkdir -p "$cache/observer"
cp "$task_root/build/uart-observer-abi.c" "$cache/observer/d35_uart_abi.c"
cp "$task_root/build/uart-state-observer.c" "$cache/observer/d35_uart_state.c"
cp "$private/uart-state-guards.h" "$cache/observer/"
printf 'obj-m := d35_uart_abi.o d35_uart_state.o\nccflags-y := -march=armv7-a -marm\n' > "$cache/observer/Makefile"
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- M="$cache/observer" modules > "$cache/observer.log" 2>&1
cp "$cache/observer/d35_uart_abi.ko" "$cache/observer/d35_uart_state.ko" "$private/"
cp "$kernel/.config" "$private/reconstructed.config"
cp "$cache/observer.log" "$private/build.log"
printf 'Offline ABI and snapshot modules built; not installation-qualified.\n'
