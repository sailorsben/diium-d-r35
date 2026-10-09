#!/bin/sh
# One boot only. Read the actual splash owner; never signal/init a display.
BASE=${D35_BOOT_PROBE_BASE:-/usr/retro/vesper-boot-probe}
PROC=${D35_BOOT_PROBE_PROC:-/proc}
ROOT=${D35_BOOT_PROBE_ROOT:-}
[ -f "$BASE/armed" ] || exit 0
mv "$BASE/armed" "$BASE/consumed" || exit 1
mkdir -p "$BASE/results" || exit 1
OUT="$BASE/results"
sync
exec > "$OUT/probe.log" 2>&1
printf 'probe_version=1 display_calls=none executable_launches=none\n'
for NAME in init.rc init.project.rc etc/inittab etc/sdmount.sh; do
  if [ -r "$ROOT/$NAME" ]; then
    case "$NAME" in
      init.rc) TARGET=init.rc;; init.project.rc) TARGET=init.project.rc;;
      etc/inittab) TARGET=etc_inittab;; etc/sdmount.sh) TARGET=etc_sdmount.sh;;
      mounts) TARGET=mounts;; self/mountinfo) TARGET=self_mountinfo;;
      1/mountinfo) TARGET=1_mountinfo;; uptime) TARGET=uptime;;
    esac
    cat "$ROOT/$NAME" > "$OUT/$TARGET"
    printf 'boot_source=%s read_status=%s\n' "$NAME" "$?"
  fi
done
for NAME in mounts self/mountinfo 1/mountinfo uptime; do
  if [ -r "$PROC/$NAME" ]; then
    case "$NAME" in
      init.rc) TARGET=init.rc;; init.project.rc) TARGET=init.project.rc;;
      etc/inittab) TARGET=etc_inittab;; etc/sdmount.sh) TARGET=etc_sdmount.sh;;
      mounts) TARGET=mounts;; self/mountinfo) TARGET=self_mountinfo;;
      1/mountinfo) TARGET=1_mountinfo;; uptime) TARGET=uptime;;
    esac
    cat "$PROC/$NAME" > "$OUT/proc-$TARGET"
  fi
done
ROUND=0
ROUNDS=${D35_BOOT_PROBE_ROUNDS:-3}
while [ "$ROUND" -lt "$ROUNDS" ]; do
  printf 'round=%s\n' "$ROUND"
  for ENTRY in "$PROC"/[0-9]*; do
    [ -r "$ENTRY/comm" ] || continue
    IFS= read -r COMM < "$ENTRY/comm" || continue
    [ "$COMM" = showlogo ] || continue
    PID=${ENTRY##*/}
    printf 'active_showlogo_pid=%s\n' "$PID"
    [ -f "$OUT/showlogo-$PID-seen" ] && continue
    printf 'seen\n' > "$OUT/showlogo-$PID-seen"
    for NAME in comm cmdline maps status; do
      cat "$ENTRY/$NAME" > "$OUT/showlogo-$PID-$NAME" 2>> "$OUT/probe.log"
    done
    ls -l "$ENTRY/exe" > "$OUT/showlogo-$PID-exe-link" 2>&1
    cat "$ENTRY/exe" > "$OUT/showlogo-$PID.elf"
    printf 'executable_copy_status=%s\n' "$?"
  done
  ROUND=$((ROUND + 1))
  [ "$ROUND" -lt "$ROUNDS" ] && sleep 1
done
# Read-only firmware route inventory; do not open raw devices.
for NAME in partitions mtd cmdline; do
  [ -r "$PROC/$NAME" ] && cat "$PROC/$NAME" > "$OUT/proc-$NAME"
done
for NAME in /dev /sys/block /sys/class/mtd /bin /sbin /system/bin /system/sbin; do
  printf '\nDIRECTORY %s\n' "$NAME"
  ls -l "$NAME" 2>&1
done
for NAME in /sysinit /bin/busybox; do
  [ -r "$NAME" ] || continue
  case "$NAME" in /sysinit) TARGET=sysinit;; /bin/busybox) TARGET=busybox;; esac
  cat "$NAME" > "$OUT/$TARGET"
done
printf 'capture_complete=1\n' 
sync
