#!/bin/sh
# Called synchronously by normal retro/init on every boot, before any test/main.
BASE=/usr/retro/uart-fix1
# Rollback switch is intentionally checked before opening/loading any payload.
if [ -f "$BASE/disabled" ]; then
  exit 0
fi
if [ ! -f "$BASE/d35_uart_tx.ko" ] || [ ! -x "$BASE/uart-fix-boot" ]; then
  exit 0
fi
"$BASE/uart-fix-boot" start "$BASE/d35_uart_tx.ko" > /tmp/d35-uart-fix.log 2>&1
result=$?
printf 'version=uart-fix1 helper_exit=%s lifetime=until_detach_or_reboot\n' "$result" >> /tmp/d35-uart-fix.log
# Bounded latest boot report; logging failure does not change handler ownership.
cp /tmp/d35-uart-fix.log "$BASE/latest-boot.log" 2>/dev/null || true
case "$result" in
  0|1) exit 0 ;;
  *) exit 64 ;;
esac
