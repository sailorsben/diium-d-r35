#!/bin/sh
# Original-status capture before stock startup. Consume the one-shot before loading
# anything; following reboot is stock even if the diagnostic cannot finish.
BASE=${D35_UART_BASE:-/usr/retro/uart-tx1}
TRIGGER=${D35_UART_TRIGGER:-/usr/retro/snes-mvp}
[ -f "$TRIGGER/armed" ] || exit 0
[ ! -e "$BASE/last-launch" ] || exit 21
mv "$TRIGGER/armed" "$BASE/last-launch" || exit 22
printf 'UART TX1 original/corrected/restored TX test; marker consumed\n' > "$BASE/startup.log"
sync
"$BASE/uart-tx-owner" "$BASE/d35_uart_tx.ko" "$BASE/observer.txt" > "$BASE/owner.err" 2>&1 &
OWNER=$!
LEFT=45
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
if [ "$RESULT" -ne 0 ]; then
    printf 'owner_exit=%s; stock withheld; power-cycle and return card\n' "$RESULT" >> "$BASE/startup.log"
    sync
    # Keep stock startup behind the synchronous hook on uncertain restoration.
    # The consumed marker makes the following power-cycle take the stock path.
    while :; do sleep 10; done
fi
printf 'owner_exit=0; returning to stock startup\n' >> "$BASE/startup.log"
sync
exit "$RESULT"
