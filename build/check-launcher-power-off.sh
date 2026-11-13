#!/bin/sh
set -eu

script=$1
fixture=$2
mkdir -p "$fixture"

# Load the production function. Stub only the system commands that would
# change a mount or swap device. The function reads real proc-shaped files.
eval "$(sed '/^PATH=/,$d' "$script")"
swapoff() {
    printf 'swapoff %s\n' "$*" >> "$fixture/actions"
    [ "$scenario" != swap-error ]
}
sync() { printf 'sync\n' >> "$fixture/actions"; }
mount() {
    [ "$*" = '-t vfat -o remount,ro /dev/sdcardb1 /media/sdcardb1' ]
    printf 'mount\n' >> "$fixture/actions"
    [ "$scenario" != mount-error ] || return 1
    if [ "$scenario" != still-rw ]; then
        cp "$fixture/read-only" "$fixture/mounts"
    fi
}

printf '/dev/sdcardb1 /media/sdcardb1 vfat ro,relatime 0 0\n/dev/sdcardb1 /usr/retro vfat rw,relatime 0 0\n' > "$fixture/read-only"
printf 'Filename Type Size Used Priority\n/usr/retro/swapfile file 32768 1 -2\n' > "$fixture/swaps"
for scenario in success swap-error mount-error still-rw unknown-card; do
    printf '/dev/sdcardb1 /media/sdcardb1 vfat rw,relatime 0 0\n/dev/sdcardb1 /usr/retro vfat rw,relatime 0 0\n' > "$fixture/mounts"
    : > "$fixture/actions"
    if [ "$scenario" = unknown-card ]; then
        printf '/dev/other /usr/retro vfat rw 0 0\n' > "$fixture/mounts"
    fi
    status=0
    prepare_card "$fixture/mounts" "$fixture/swaps" "$fixture/receipt" || status=$?
    case "$scenario" in
        success) [ "$status" = 0 ] ;;
        still-rw) [ "$status" = 2 ] ;;
        *) [ "$status" = 1 ] ;;
    esac
    case "$scenario" in
        swap-error) expected='swapoff /usr/retro/swapfile' ;;
        unknown-card) expected= ;;
        *) expected=$(printf 'swapoff /usr/retro/swapfile\nsync\nmount') ;;
    esac
    [ "$(cat "$fixture/actions")" = "$expected" ]
done
printf '%s\n' 'PASS exact card mount, targeted swapoff, sync, readonly verification, and failure stops'
