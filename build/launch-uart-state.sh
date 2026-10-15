#!/bin/sh
# Snapshot preflight before stock startup. Consume the one-shot before loading
# anything; following reboot is stock even if the diagnostic cannot finish.
BASE=${D35_UART_BASE:-/usr/retro/uart-state1}
TRIGGER=${D35_UART_TRIGGER:-/usr/retro/snes-mvp}
[ -f "$TRIGGER/armed" ] || exit 0
[ ! -e "$BASE/last-launch" ] || exit 21
mv "$TRIGGER/armed" "$BASE/last-launch" || exit 22
printf 'UART state1 snapshot-only preflight; marker consumed\n' > "$BASE/startup.log"
sync
"$BASE/uart-state-owner" "$BASE/d35_uart_state.ko" "$BASE/observer.txt" > "$BASE/owner.err" 2>&1 &
OWNER=$!
LEFT=20
while kill -0 "$OWNER" 2>/dev/null && [ "$LEFT" -gt 0 ]; do
    sleep 1
    LEFT=$((LEFT-1))
done
if kill -0 "$OWNER" 2>/dev/null; then
    printf 'owner timeout; requesting bounded cleanup\n' >> "$BASE/startup.log"
    kill -TERM "$OWNER" 2>/dev/null
    sleep 2
    if kill -0 "$OWNER" 2>/dev/null; then kill -KILL "$OWNER" 2>/dev/null; fi
fi
wait "$OWNER"
RESULT=$?
printf 'owner_exit=%s; returning to stock startup\n' "$RESULT" >> "$BASE/startup.log"
sync
exit "$RESULT"
