#!/bin/sh
# Read-only libretro replays. No native PCM or display owner is started here.
set -u
LAB=${D35_RASTER_LAB:-/usr/retro/snes-raster-test1}
MVP=${D35_RASTER_MVP:-/usr/retro/snes-mvp}
FROZEN=${D35_RASTER_FROZEN:-/usr/retro/snes-fivegame-kernel2}
PROC=${D35_RASTER_PROC:-/proc}
STOP=${D35_RASTER_SPLASH_STOP:-/tmp/vrtemu.log}
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
mkdir -p "$LAB/results" && mkdir "$OUT" || exit 1
printf 'profile=raster-core-a7-1\nnative_pcm=0\nnative_display=0\n' > "$OUT/wrapper.log"

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
        [ "$ZOMBIE" = 1 ] || return 0
    done
    return 1
}

: > "$STOP" || exit 1
WAITED=0
while active_splash; do
    if [ "$WAITED" -ge 5 ]; then
        printf 'splash_timeout\n' >> "$OUT/wrapper.log"
        sync
        exit 1
    fi
    sleep 1
    WAITED=$((WAITED+1))
done
printf 'splash_released waited=%s\n' "$WAITED" >> "$OUT/wrapper.log"
if [ -r "$PROC/cpuinfo" ]; then cat "$PROC/cpuinfo" > "$OUT/cpuinfo.txt"; fi
if [ -r "$PROC/meminfo" ]; then cat "$PROC/meminfo" > "$OUT/meminfo.txt"; fi
export LD_LIBRARY_PATH=/lib:/usr/lib:/system/lib:/usr/retro/libs

run_pair() {
    GAME=$1
    VARIANT=$2
    case "$GAME" in
        003) COLD=8656; MODE=both-cold-off-device;;
        *) COLD=0; MODE=device;;
    esac
    NAME="$GAME-$VARIANT"
    printf 'begin %s\n' "$NAME" >> "$OUT/wrapper.log"
    sync
    "$LAB/pair" "$FROZEN/plus-a7.so" "$LAB/cores/$VARIANT.so" "$FROZEN/cases/$GAME" "$COLD" "$MODE" \
        > "$OUT/$NAME.csv" 2> "$OUT/$NAME.log"
    RESULT=$?
    printf 'end %s rc=%s\n' "$NAME" "$RESULT" >> "$OUT/wrapper.log"
    sync
    return "$RESULT"
}

# Price the two Star Fox contenders first, then check the same binaries on
# the non-Mode-2 fixtures. The sprite probes cover their two clearest wins.
for GAME_ID in 003 000 001 002 004; do
    run_pair "$GAME_ID" raster-offset || exit "$?"
    run_pair "$GAME_ID" raster-offset-full || exit "$?"
done
run_pair 000 raster-objects-wide || exit "$?"
run_pair 002 raster-objects || exit "$?"
printf 'complete pairs=12\n' >> "$OUT/wrapper.log"
sync
