#!/bin/sh
# One-shot comparison using the qualified board and cold Star Fox replay.
LAB=${D35_DISPLAY_LAB:-/usr/retro/snes-shell-display1}
MVP=${D35_DISPLAY_MVP:-/usr/retro/snes-mvp}
PROC=${D35_DISPLAY_PROC:-/proc}
STOP=${D35_DISPLAY_STOP:-/tmp/vrtemu.log}
FIXTURES=${D35_DISPLAY_FIXTURES:-/usr/retro/snes-fivegame-kernel2}
[ -f "$LAB/armed" ] && [ -f "$MVP/armed" ] || exit 0
mv "$MVP/armed" "$LAB/last-boot-marker" || exit 1
mv "$LAB/armed" "$LAB/last-launch" || exit 1
sync

BOOT=unknown
if [ -r "$PROC/sys/kernel/random/boot_id" ]; then
    IFS= read -r BOOT < "$PROC/sys/kernel/random/boot_id" || BOOT=unknown
fi
case "$BOOT" in *[!0-9a-f-]*|'') BOOT=unknown;; esac
OUT="$LAB/results/run-$BOOT-$$"
mkdir -p "$OUT" || exit 1
LOG="$OUT/wrapper.log"
printf 'profile=stock-shell-display1\nframeskip=off\n' > "$LOG"

active_splash() {
    for entry in "$PROC"/[0-9]*; do
        [ -r "$entry/comm" ] || continue
        IFS= read -r name < "$entry/comm" || continue
        [ "$name" = showlogo ] || continue
        zombie=0
        if [ -r "$entry/status" ]; then
            while IFS= read -r line; do
                case "$line" in State:*Z*) zombie=1; break;; esac
            done < "$entry/status"
        fi
        [ "$zombie" = 1 ] || return 0
    done
    return 1
}

: > "$STOP" || exit 1
waited=0
while active_splash; do
    if [ "$waited" -ge 5 ]; then
        printf 'splash_timeout\n' >> "$LOG"
        sync
        exit 1
    fi
    sleep 1
    waited=$((waited+1))
done
printf 'splash_released waited=%s\n' "$waited" >> "$LOG"
unset D35_ABILITY_MOCK D35_MVP_NO_PACING D35_FULL_HOST_FIXTURE D35_FIVE_ORACLE D35_FFVI_RUN_LIMIT
export LD_LIBRARY_PATH=/lib:/usr/lib:/system/lib:/usr/retro/libs
export D35_DISPLAY_FIXTURES="$FIXTURES"

run_window() {
    name=$1
    dir="$OUT/$name"
    mkdir "$dir" || return 72
    ram="/tmp/shell-display-$$-$name"
    printf 'begin %s pcm=%s reuse=%s\n' "$name" "$2" "$3" >> "$LOG"
    sync
    D35_MEASURE_DISPLAY="$2" D35_IDENTICAL_VIDEO_REUSE="$3" \
        D35_MVP_PCM_TRACE_FILE="$ram.pcm" "$LAB/display-runner" --supervise "$dir" "$LAB" \
        "$FIXTURES/cases/003/game.sfc" > "$ram.log" 2>&1
    rc=$?
    cp "$ram.log" "$dir/console.log" || rc=72
    if [ -f "$ram.pcm" ]; then cp "$ram.pcm" "$dir/pcm-flight.txt" || rc=72; fi
    printf 'end %s rc=%s\n' "$name" "$rc" >> "$LOG"
    sync
    return "$rc"
}

handle_result() {
    case "$1" in
        0|1) return "$1";;
        5) exit 0;;
        *)
            printf 'child_cleanup_unverified reboot_required=1 next_boot=stock\n' >> "$LOG"
            sync
            while :; do sleep 1; done;;
    esac
}

run_window display-control 1 0
handle_result "$?" || exit 1
run_window display-reuse 1 1
handle_result "$?" || exit 1
run_window pcm-control 0 0
handle_result "$?"
run_window pcm-reuse 0 1
handle_result "$?"
printf 'complete\n' >> "$LOG"
sync
