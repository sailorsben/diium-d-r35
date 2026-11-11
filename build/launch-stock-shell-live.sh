#!/bin/sh
# The stock init calls this before starting its one frontend supervisor.
RETRO=${D35_LAUNCHER_RETRO:-/usr/retro}
BASE="$RETRO/d35-launcher1"
MVP="$RETRO/snes-mvp"
PROC=${D35_LAUNCHER_PROC:-/proc}
STOP=${D35_LAUNCHER_SPLASH_STOP:-/tmp/vrtemu.log}
BUSYBOX=${D35_LAUNCHER_BUSYBOX:-/bin/busybox}

[ -f "$BASE/armed" ] && [ -f "$MVP/armed" ] || exit 0
mv "$MVP/armed" "$BASE/last-boot-marker" || exit 1
mv "$BASE/armed" "$BASE/last-launch" || exit 1
sync

LOG="$BASE/last-launcher.log"
printf 'launcher=d35-launcher1\n' > "$LOG" || exit 1
if [ ! -x "$BASE/vrtemu" ] || [ ! -r "$BASE/libs/d35-snes.so" ] ||
   [ ! -r "$BASE/d35-menu.pcm" ] || [ ! -x "$RETRO/vrtemu" ]; then
    printf 'payload_missing\n' >> "$LOG"
    sync
    exit 1
fi

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

ART="$BASE/ui_en.bkp"
STOCK_ART="$RETRO/ui_en.bkp"
art_bound=0
if [ -f "$ART" ]; then
    if ! "$BUSYBOX" mount -o bind "$ART" "$STOCK_ART" >> "$LOG" 2>&1; then
        printf 'english_art_mount_failed\n' >> "$LOG"
        sync
        exit 1
    fi
    art_bound=1
fi

if "$BUSYBOX" mount -o bind "$BASE/vrtemu" "$RETRO/vrtemu" >> "$LOG" 2>&1; then
    printf 'frontend_bound_for_this_boot=1 splash_wait_seconds=%s\n' "$waited" >> "$LOG"
    printf 'english_art_bound_for_this_boot=%s\n' "$art_bound" >> "$LOG"
    sync
    exit 0
fi
if [ "$art_bound" = 1 ]; then
    "$BUSYBOX" umount "$STOCK_ART" >> "$LOG" 2>&1
fi
printf 'frontend_mount_failed\n' >> "$LOG"
sync
exit 1
