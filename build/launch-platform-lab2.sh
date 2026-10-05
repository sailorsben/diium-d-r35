#!/bin/sh
# Isolated one-shot lab, invoked by the already-qualified SNES boot seam.
LAB=${D35_LAB_BASE:-/usr/retro/platform-lab}
MVP=${D35_MVP_BASE:-/usr/retro/snes-mvp}
[ -f "$LAB/armed" ] && [ -f "$MVP/armed" ] || exit 0
mv "$LAB/armed" "$LAB/last-launch" || exit 1
mv "$MVP/armed" "$MVP/last-launch-lab" || exit 1
PROC=${D35_LAB_PROC_ROOT:-/proc}
BOOT=unknown
if [ -r "$PROC/sys/kernel/random/boot_id" ]; then
  IFS= read -r BOOT < "$PROC/sys/kernel/random/boot_id" || BOOT=unknown
fi
case "$BOOT" in *[!0-9a-f-]*|'') BOOT=unknown;; esac
OUT="$LAB/results/run-$BOOT-$$"
mkdir -p "$LAB/results" || exit 1
mkdir "$OUT" || exit 1
printf 'lab2 wrapper_pid=%s\n' "$$" > "$OUT/wrapper.log"
# New directory and consumed markers persist before hardware ownership.
sync
STOP=${D35_LAB_SPLASH_STOP:-/tmp/vrtemu.log}
active_splash() {
  for ENTRY in "$PROC"/[0-9]*; do
    [ -r "$ENTRY/comm" ] || continue
    IFS= read -r COMM < "$ENTRY/comm" || continue
    [ "$COMM" = showlogo ] || continue
    ZOMBIE=0
    if [ -r "$ENTRY/status" ]; then
      while IFS= read -r LINE; do
        case "$LINE" in State:*)
          case "$LINE" in *Z*) ZOMBIE=1;; esac
          break;;
        esac
      done < "$ENTRY/status"
    fi
    [ "$ZOMBIE" = 1 ] || printf '%s ' "${ENTRY##*/}"
  done
}
if ! : > "$STOP"; then
  printf 'splash_stop_failed\n' >> "$OUT/wrapper.log"
  sync
  exit 1
fi
ACTIVE=$(active_splash)
WAIT=0
while [ -n "$ACTIVE" ] && [ "$WAIT" -lt 5 ]; do
  sleep 1
  WAIT=$((WAIT+1))
  ACTIVE=$(active_splash)
done
if [ -n "$ACTIVE" ]; then
  printf 'splash_timeout active=%s\n' "$ACTIVE" >> "$OUT/wrapper.log"
  sync
  exit 1
fi
printf 'splash_released waited_seconds=%s\n' "$WAIT" >> "$OUT/wrapper.log"
sync
export LD_LIBRARY_PATH=/lib:/usr/lib:/system/lib:/usr/retro/libs
"$LAB/platform-lab" --supervise --output "$OUT" > "$OUT/console.log" 2>&1
RESULT=$?
printf 'lab_exit=%s\n' "$RESULT" >> "$OUT/wrapper.log"
sync
if [ "$RESULT" -eq 72 ]; then
  # Forced termination may leave peripheral state unqualified. A following
  # reboot is stock; do not immediately start another display owner here.
  printf 'deadline reached; reboot required; next boot is stock\n' >> "$OUT/wrapper.log"
  sync
  while :; do sleep 1; done
fi
exit "$RESULT"
