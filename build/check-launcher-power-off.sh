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
boot_id=12345678-1234-4321-8765-123456789abc
for scenario in success swap-error mount-error still-rw unknown-card; do
    printf '/dev/sdcardb1 /media/sdcardb1 vfat rw,relatime 0 0\n/dev/sdcardb1 /usr/retro vfat rw,relatime 0 0\n' > "$fixture/mounts"
    : > "$fixture/actions"
    if [ "$scenario" = unknown-card ]; then
        printf '/dev/other /usr/retro vfat rw 0 0\n' > "$fixture/mounts"
    fi
    : > "$fixture/receipt"
    status=0
    prepare_card "$fixture/mounts" "$fixture/swaps" "$fixture/receipt" "$boot_id" || status=$?
    case "$scenario" in
        success) [ "$status" = 0 ] ;;
        still-rw) [ "$status" = 2 ] ;;
        *) [ "$status" = 1 ] ;;
    esac
    case "$scenario" in
        swap-error) expected='swapoff /usr/retro/swapfile'; receipt= ;;
        unknown-card) expected=; receipt= ;;
        *)
            expected=$(printf 'swapoff /usr/retro/swapfile\nsync\nmount')
            receipt="poweroff=requested mount=/dev/sdcardb1 boot_id=$boot_id"
            ;;
    esac
    [ "$(cat "$fixture/actions")" = "$expected" ]
    [ "$(cat "$fixture/receipt")" = "$receipt" ]
done
printf '%s\n' 'PASS exact card mount, targeted swapoff, boot-scoped receipt, sync, readonly verification, and failure stops'
