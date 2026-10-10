#!/bin/sh
# One-shot hardware bring-up. Preserve startup evidence even after power-off.
BASE=/usr/retro/snes-cost1
TRIGGER=/usr/retro/snes-mvp
if [ ! -f "$TRIGGER/armed" ]; then exit 0; fi
mv "$TRIGGER/armed" "$BASE/last-launch" || exit 1
mkdir -p "$BASE/saves"
printf 'SNES MVP 1.19-cost1 native PCM startup wrapper pid=%s\n' "$$" > "$BASE/startup.log"
: > "$BASE/runtime-platform.txt"
: > "$BASE/runtime-platform-latest.txt"
: > "$BASE/kernel-tail.txt"
: > "$BASE/diagnostic-flush.log"
printf 'build_version=1.19-cost1\nphase=wrapper_start\nwrapper_pid=%s\n' "$$" > "$BASE/last-progress.txt"
sync
# Vendor boot handoff: showlogo joytest polls /tmp/vrtemu.log, then clears,
# flips and destroys its display before creating /tmp/displogo.log. Complete
# this BEFORE InitVFB so it cannot later overwrite/free our live display.
PROC_ROOT=${D35_MVP_PROC_ROOT:-/proc}
SPLASH_STOP=${D35_MVP_SPLASH_STOP:-/tmp/vrtemu.log}
SPLASH_ACK=${D35_MVP_SPLASH_ACK:-/tmp/displogo.log}
first_lines() {
  CAPTURE_LEFT=$1
  while [ "$CAPTURE_LEFT" -gt 0 ] && IFS= read -r CAPTURE_LINE; do
    printf '%s\n' "$CAPTURE_LINE"
    CAPTURE_LEFT=$((CAPTURE_LEFT - 1))
  done
}
splash_pids() {
  for ENTRY in "$PROC_ROOT"/[0-9]*; do
    [ -r "$ENTRY/comm" ] || continue
    IFS= read -r COMM < "$ENTRY/comm" || continue
    if [ "$COMM" = showlogo ]; then
      # Zombies have already closed their display; do not wait for parent reap.
      STATE=
      if [ -r "$ENTRY/status" ]; then
        while IFS= read -r SPLASH_LINE; do
          case "$SPLASH_LINE" in State:*)
            case "$SPLASH_LINE" in *Z*) STATE=Z;; esac
            break;;
          esac
        done < "$ENTRY/status"
      fi
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
export D35_MVP_PCM_TRACE_FILE="$BASE/last-pcm-fault.txt"
# Never interpret a previous boot's PCM history as this run.
rm -f "$D35_MVP_PCM_TRACE_FILE" "$D35_MVP_PCM_TRACE_FILE.tmp" "$BASE/last-pcm-fault.txt"
RUNTIME_LOG="/tmp/snes-mvp-runtime.$$"
capture_runtime() {
  # Returned byte-tail files were empty. Keep bounded startup/errors using
  # shell builtins; tail/head/sed availability cannot erase this evidence.
  first_lines 192 < "$RUNTIME_LOG" > "$BASE/last-run.log"
}
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
capture_platform() {
  # Discovery is deliberately outside the child's lifetime. Even unsynced SD
  # writes and /proc discovery can consume the PCM owner's scheduling margin.
  {
    printf 'Platform snapshot phase=%s live_child=no\n' "$1"
    cat /proc/uptime /proc/sysvipc/shm 2>&1
    printf '\nKernel CPU/memory/interrupt samples\n'
    first_lines 16 < /proc/stat
    first_lines 24 < /proc/meminfo
    first_lines 32 < /proc/interrupts
    for ENTRY in "$PROC_ROOT"/[0-9]*; do
      [ -r "$ENTRY/comm" ] || continue
      IFS= read -r COMM < "$ENTRY/comm" || continue
      case "$COMM" in wdt|power_key)
        printf '\nHelper %s %s\n' "$COMM" "$ENTRY"
        cat "$ENTRY/stat" "$ENTRY/wchan" "$ENTRY/syscall" 2>&1;;
      esac
    done
    ps 2>&1 | first_lines 80
  } > "$BASE/runtime-platform-latest.txt.tmp"
  mv "$BASE/runtime-platform-latest.txt.tmp" "$BASE/runtime-platform-latest.txt"
  cat "$BASE/runtime-platform-latest.txt" >> "$BASE/runtime-platform.txt"
}
capture_platform pre_child
printf 'diagnostics=outside_child_lifetime ram_progress=once_per_second background_monitor=none\n' >> "$BASE/diagnostic-flush.log"
printf 'starting child startup deadline=%ss\n' "$DEADLINE" >> "$BASE/startup.log"
sync
IFS= read -r D35_COST_ROM < "$BASE/ROM-PATH.txt" || exit 1
[ -f "$D35_COST_ROM" ] || exit 1
"$BASE/unit-suite" "$BASE" "$BASE/measure-core.so" "$D35_COST_ROM" "$BASE/replay.state" > "$RUNTIME_LOG" 2>&1 &
CHILD=$!
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
  capture_runtime
  sync
  kill -TERM "$CHILD" 2>/dev/null
  sleep 1
  if kill -0 "$CHILD" 2>/dev/null; then kill -KILL "$CHILD" 2>/dev/null; fi
  # Never start the stock display owner while a stuck MVP still exists.
fi
# No background diagnostic process, platform discovery or card checkpoints
# while the child is alive. The runner keeps progress/phase records in RAM;
# native faults persist their own bounded trace before returning an error.
wait "$CHILD"
RESULT=$?
printf 'child pid=%s startup deadline=%ss\n' "$CHILD" "$DEADLINE" >> "$BASE/startup.log"
printf 'process exited status=%s ready=%s\n' "$RESULT" "$(test -f "$D35_MVP_READY_FILE" && printf yes || printf no)" >> "$BASE/startup.log"
capture_platform post_child
{ printf 'Bounded first 128 kernel lines (no tail dependency)\n';
  dmesg 2>&1 | first_lines 128; } > "$BASE/kernel-tail.txt.tmp"
mv "$BASE/kernel-tail.txt.tmp" "$BASE/kernel-tail.txt"
capture_runtime
copy_progress
printf 'final_copies=after_child_exit\n' >> "$BASE/diagnostic-flush.log"
rm -f "$D35_MVP_READY_FILE" "$RUNTIME_LOG" "$D35_MVP_PROGRESS_FILE" "$D35_MVP_PROGRESS_FILE.tmp"
sync
exit "$RESULT"
