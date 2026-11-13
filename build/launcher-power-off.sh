#!/bin/sh
# Run from Settings after game exit. Return success only after the FAT
# filesystem is read-only, including access through its bind mount.

prepare_card() {
    mounts=$1
    swaps=$2
    log=$3
    device=
    media=
    while read -r source target type options rest; do
        if [ "$target" = /usr/retro ] && [ "$type" = vfat ]; then
            device=$source
        fi
    done < "$mounts"
    case "$device" in /dev/sdcard*) ;; *) return 1 ;; esac
    while read -r source target type options rest; do
        if [ "$source" = "$device" ] && [ "$type" = vfat ]; then
            case "$target" in /media/sdcard*) media=$target ;; esac
        fi
    done < "$mounts"
    [ -n "$media" ] || return 1

    while read -r file rest; do
        case "$file" in
            /usr/retro/swapfile|"$media"/retro/swapfile)
                swapoff "$file" || return 1
                ;;
        esac
    done < "$swaps"

    printf 'poweroff=requested mount=%s\n' "$device" > "$log" || return 1
    sync || return 1
    # Use the full FAT mount. A read-only bind remount alone would leave
    # the same card writable through /media.
    mount -t vfat -o remount,ro "$device" "$media" || return 1
    while read -r source target type options rest; do
        [ "$source" = "$device" ] || continue
        # Older Linux reports the effective superblock RO state in
        # mountinfo even when a bind mount retains its own rw flag.
        if [ "$target" = "$media" ]; then
            case ",$options," in *,ro,*) return 0 ;; esac
        fi
    done < "$mounts"
    return 2
}

PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH
cd / || exit 1
prepare_card /proc/mounts /proc/swaps /usr/retro/d35-launcher1/power-off.log
