#!/bin/sh
# One-shot SD-stage animation; internal firmware is unchanged.
BASE=${D35_VESPER_BASE:-/usr/retro/vesper-boot}
PROC=${D35_VESPER_PROC:-/proc}
STOP=${D35_VESPER_STOP:-/tmp/vrtemu.log}
[ -f "$BASE/armed" ] || exit 0
mv "$BASE/armed" "$BASE/consumed" || exit 1
exec > "$BASE/startup.log" 2>&1
active() {
  for ENTRY in "$PROC"/[0-9]*; do
    [ -r "$ENTRY/comm" ] || continue
    IFS= read -r COMM < "$ENTRY/comm" || continue
    [ "$COMM" = showlogo ] || continue
    STATE=
    while IFS= read -r LINE; do
      case "$LINE" in State:*) case "$LINE" in *Z*) STATE=Z;; esac; break;; esac
    done < "$ENTRY/status"
    [ "$STATE" = Z ] || printf '%s ' "${ENTRY##*/}"
  done
}
release() {
  : > "$STOP" || return 1
  LEFT=5
  while [ -n "$(active)" ] && [ "$LEFT" -gt 0 ]; do
    sleep 1; LEFT=$((LEFT - 1))
  done
  [ -z "$(active)" ]
}
printf 'version=1 phase=stock_release\n'
if ! release; then printf 'stock_release_timeout; animation refused\n'; sync; exit 1; fi
printf 'stock_released=1\n'
rm -f "$STOP" || exit 1
"${D35_VESPER_EXECUTABLE:-/usr/retro/showlogo}" &
CHILD=$!
printf 'phase=vesper_started pid=%s\n' "$CHILD"
sleep 3
if ! release; then
  printf 'vesper_release_timeout; waiting for owned child before launcher\n'
fi
wait "$CHILD"
STATUS=$?
printf 'phase=complete child_exit=%s display_owner_reaped=1\n' "$STATUS"
sync
exit "$STATUS"
