#!/bin/sh
# Internal rootfs owner. No card payload is needed to attach the correction.
BASE=/d35-uart
READY=/tmp/d35-uart-firmware.ready
STATUS=/proc/d35_uart_tx
LOG=/tmp/d35-uart-firmware.log
IDENTITY=UART_MODULE_IDENTITY
case "$1" in
  verify)
    if [ ! -f "$READY" ]; then
      [ ! -e "$STATUS" ] && exit 1
      exit 64
    fi
    IFS= read -r identity < "$READY" || exit 64
    [ "$identity" = "$IDENTITY" ] || exit 64
    IFS= read -r status < "$STATUS" || exit 64
    case "$status" in 'version=4 result=0 irq=19 attached=1 '*) ;; *) exit 64 ;; esac
    case " $status " in *' fault=0 '*) ;; *) exit 64 ;; esac
    case " $status " in *' bypass=0 '*) ;; *) exit 64 ;; esac
    case " $status " in *' cap=0 '*) ;; *) exit 64 ;; esac
    exit 0 ;;
  start)
    # A powered-off card may request bypass without altering internal firmware.
    [ -f /usr/retro/uart-fix1/disabled ] && exit 0
    "$BASE/uart-fix-boot" start "$BASE/d35_uart_tx.ko" > "$LOG" 2>&1
    result=$?
    printf 'version=uart-firmware1 helper_exit=%s\n' "$result" >> "$LOG"
    case "$result" in
      0) printf '%s\n' "$IDENTITY" > "$READY" || exit 64; exit 0 ;;
      1) exit 0 ;;
      *) exit 64 ;;
    esac ;;
  *) exit 64 ;;
esac
