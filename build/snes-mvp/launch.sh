#!/bin/sh
# One-shot hardware bring-up. Preserve startup evidence even after power-off.
BASE=${D35_MVP_BASE:-/usr/retro/snes-mvp}
if [ ! -f "$BASE/armed" ]; then exit 0; fi
mv "$BASE/armed" "$BASE/last-launch" || exit 1
mkdir -p "$BASE/saves"
printf 'SNES MVP 1.7 diagnostic startup wrapper pid=%s\n' "$$" > "$BASE/startup.log"
: > "$BASE/runtime-platform.txt"
: > "$BASE/runtime-platform-latest.txt"
: > "$BASE/kernel-tail.txt"
: > "$BASE/diagnostic-flush.log"
printf 'build_version=1.7\nphase=wrapper_start\nwrapper_pid=%s\n' "$$" > "$BASE/last-progress.txt"
sync
# Vendor boot handoff: showlogo joytest polls /tmp/vrtemu.log, then clears,
# flips and destroys its display before creating /tmp/displogo.log. Complete
# this BEFORE InitVFB so it cannot later overwrite/free our live display.
PROC_ROOT=${D35_MVP_PROC_ROOT:-/proc}
SPLASH_STOP=${D35_MVP_SPLASH_STOP:-/tmp/vrtemu.log}
SPLASH_ACK=${D35_MVP_SPLASH_ACK:-/tmp/displogo.log}
splash_pids() {
  for ENTRY in "$PROC_ROOT"/[0-9]*; do
    [ -r "$ENTRY/comm" ] || continue
    IFS= read -r COMM < "$ENTRY/comm" || continue
    if [ "$COMM" = showlogo ]; then
      # Zombies have already closed their display; do not wait for parent reap.
      STATE=$(sed -n 's/^State:[[:space:]]*\([A-Z]\).*/\1/p' "$ENTRY/status" 2>/dev/null)
      [ "$STATE" = Z ] || printf '%s ' "${ENTRY##*/}"
    fi
  done
}
ps > "$BASE/startup-processes.txt" 2>&1
# Read-only copies of the boot helpers let us verify their contract on return.
if [ "$PROC_ROOT" = /proc ]; then
  for HELPER in wdt power_key; do
    [ -f "/$HELPER" ] && cp "/$HELPER" "$BASE/platform-$HELPER"
  done
  {
    printf 'Boot identity\n'
    cat /proc/sys/kernel/random/boot_id /proc/uptime /proc/sysvipc/shm 2>&1
  } > "$BASE/startup-platform.txt"
fi
SPLASH=$(splash_pids)
printf 'splash handoff begin active_pids=%s stop=%s ack=%s\n' "$SPLASH" "$SPLASH_STOP" "$SPLASH_ACK" >> "$BASE/startup.log"
if ! : > "$SPLASH_STOP"; then
  printf 'splash stop signal failed; MVP not started\n' >> "$BASE/startup.log"
  sync
  exit 1
fi
SPLASH_WAIT=0
while [ -n "$SPLASH" ] && [ "$SPLASH_WAIT" -lt 5 ]; do
  sleep 1
  SPLASH_WAIT=$((SPLASH_WAIT + 1))
  SPLASH=$(splash_pids)
done
if [ -n "$SPLASH" ]; then
  printf 'splash handoff timeout active_pids=%s; MVP not started\n' "$SPLASH" >> "$BASE/startup.log"
  sync
  exit 1
fi
if [ -f "$SPLASH_ACK" ]; then SPLASH_RELEASED=yes; else SPLASH_RELEASED=absent; fi
printf 'splash handoff complete active_pids=none release_ack=%s waited=%ss\n' "$SPLASH_RELEASED" "$SPLASH_WAIT" >> "$BASE/startup.log"
sync
export LD_LIBRARY_PATH=/lib:/usr/lib:/system/lib:/usr/retro/libs
export D35_MVP_STARTUP_LOG="$BASE/startup.log"
export D35_MVP_READY_FILE="/tmp/snes-mvp-ready.$$"
export D35_MVP_PROGRESS_FILE="/tmp/snes-mvp-progress.$$"
RUNTIME_LOG="/tmp/snes-mvp-runtime.$$"
copy_progress() {
  [ -f "$D35_MVP_PROGRESS_FILE" ] || return 0
  if cp "$D35_MVP_PROGRESS_FILE" "$BASE/last-progress.txt.tmp"; then
    [ ! -f "$BASE/last-progress.txt" ] || mv "$BASE/last-progress.txt" "$BASE/last-progress.previous"
    mv "$BASE/last-progress.txt.tmp" "$BASE/last-progress.txt"
  fi
}
DEADLINE=${D35_MVP_STARTUP_SECONDS:-20}
case "$DEADLINE" in ''|*[!0-9]*) DEADLINE=20;; esac
if [ "$DEADLINE" -lt 2 ] || [ "$DEADLINE" -gt 30 ]; then DEADLINE=20; fi
"$BASE/snes-mvp" --base "$BASE" --core "$BASE/plus-a7.so" > "$RUNTIME_LOG" 2>&1 &
CHILD=$!
printf 'child pid=%s startup deadline=%ss\n' "$CHILD" "$DEADLINE" >> "$BASE/startup.log"
ELAPSED=0
while kill -0 "$CHILD" 2>/dev/null && [ ! -f "$D35_MVP_READY_FILE" ] && [ "$ELAPSED" -lt "$DEADLINE" ]; do
  sleep 1
  ELAPSED=$((ELAPSED + 1))
done
if kill -0 "$CHILD" 2>/dev/null && [ ! -f "$D35_MVP_READY_FILE" ]; then
  printf 'STARTUP TIMEOUT after %ss; capturing before termination\n' "$ELAPSED" >> "$BASE/startup.log"
  {
    for TASK in /proc/"$CHILD"/task/*; do
      [ -d "$TASK" ] || continue
      printf '\nTask %s\n' "$TASK"
      for FIELD in status wchan syscall stack; do
        printf '\n%s\n' "$FIELD"
        cat "$TASK/$FIELD" 2>&1
      done
    done
    printf '\nProcess inventory\n'
    ps 2>&1
  } > "$BASE/startup-stall.txt"
  # Bounded copies: console output stays in RAM during normal play.
  tail -c 32768 "$RUNTIME_LOG" > "$BASE/last-run.log"
  sync
  kill -TERM "$CHILD" 2>/dev/null
  sleep 1
  if kill -0 "$CHILD" 2>/dev/null; then kill -KILL "$CHILD" 2>/dev/null; fi
  # Never start the stock display owner while a stuck MVP still exists.
fi
# Bounded post-ready snapshots survive a reset or a hung display teardown.
# No monitoring is left running throughout an ordinary gaming session.
(
  MONITOR_SLEEP=
  monitor_stop() {
    if [ -n "$MONITOR_SLEEP" ]; then
      kill "$MONITOR_SLEEP" 2>/dev/null
      wait "$MONITOR_SLEEP" 2>/dev/null
    fi
    exit 0
  }
  trap monitor_stop TERM INT
  INDEX=0
  # Keep the first three snapshots, then one bounded latest snapshot for five
  # minutes. No per-frame SD writes; RAM progress is published once a second.
  while [ "$INDEX" -lt 63 ]; do
    case "$INDEX" in 0) DELAY=2;; *) DELAY=5;; esac
    sleep "$DELAY" &
    MONITOR_SLEEP=$!
    wait "$MONITOR_SLEEP" || exit 0
    MONITOR_SLEEP=
    kill -0 "$CHILD" 2>/dev/null || exit 0
    IFS=' ' read -r FLUSH_BEGIN UNUSED_IDLE < /proc/uptime
    {
      printf '\nRuntime snapshot child=%s delay=%ss\n' "$CHILD" "$DELAY"
      cat /proc/uptime /proc/sysvipc/shm 2>&1
      for TASK in /proc/"$CHILD"/task/*; do
        [ -d "$TASK" ] || continue
        printf '\nTask %s\n' "$TASK"
        cat "$TASK/status" "$TASK/wchan" "$TASK/syscall" "$TASK/stat" 2>&1
      done
      printf '\nKernel CPU/memory/interrupt samples\n'
      # This firmware has sed (used by the splash handoff), but no head.
      sed -n '1,16p' /proc/stat 2>&1
      sed -n '1,24p' /proc/meminfo 2>&1
      sed -n '1,32p' /proc/interrupts 2>&1
      for ENTRY in "$PROC_ROOT"/[0-9]*; do
        [ -r "$ENTRY/comm" ] || continue
        IFS= read -r COMM < "$ENTRY/comm" || continue
        case "$COMM" in wdt|power_key)
          printf '\nHelper %s %s\n' "$COMM" "$ENTRY"
          cat "$ENTRY/stat" "$ENTRY/wchan" "$ENTRY/syscall" 2>&1;;
        esac
      done
      ps 2>&1 | sed -n '1,80p'
    } > "$BASE/runtime-platform-latest.txt.tmp"
    mv "$BASE/runtime-platform-latest.txt.tmp" "$BASE/runtime-platform-latest.txt"
    if [ "$INDEX" -lt 3 ]; then cat "$BASE/runtime-platform-latest.txt" >> "$BASE/runtime-platform.txt"; fi
    dmesg 2>&1 | tail -c 16384 > "$BASE/kernel-tail.txt.tmp"
    mv "$BASE/kernel-tail.txt.tmp" "$BASE/kernel-tail.txt"
    copy_progress
    tail -c 32768 "$RUNTIME_LOG" > "$BASE/last-run.log"
    sync
    IFS=' ' read -r FLUSH_END UNUSED_IDLE < /proc/uptime
    printf 'snapshot=%s begin_uptime=%s end_after_sync_uptime=%s\n' "$INDEX" "$FLUSH_BEGIN" "$FLUSH_END" >> "$BASE/diagnostic-flush.log"
    INDEX=$((INDEX + 1))
  done
) &
MONITOR=$!
wait "$CHILD"
RESULT=$?
kill "$MONITOR" 2>/dev/null
wait "$MONITOR" 2>/dev/null
printf 'process exited status=%s ready=%s\n' "$RESULT" "$(test -f "$D35_MVP_READY_FILE" && printf yes || printf no)" >> "$BASE/startup.log"
tail -c 32768 "$RUNTIME_LOG" > "$BASE/last-run.log"
copy_progress
rm -f "$D35_MVP_READY_FILE" "$RUNTIME_LOG" "$D35_MVP_PROGRESS_FILE" "$D35_MVP_PROGRESS_FILE.tmp"
sync
exit "$RESULT"
