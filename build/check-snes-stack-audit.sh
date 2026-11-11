#!/bin/sh
# Exact frozen outputs followed by separately timed same-binary toggle pairs.
set -eu
test "$#" -ge 2
cd "$(dirname "$0")/.."
out=$(realpath "$1")
shift
flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
for test in replay pair; do
    arm-linux-gnueabihf-gcc -std=gnu11 -O2 $flags -DUSE_BLARGG_APU -DD35_AUDIT_STATE -Wall -Wextra -Werror -no-pie -nostdlib \
        -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o \
        "build/snes-throughput-$test.c" -Lbuild/sysroot/lib \
        -Wl,--no-as-needed -l:libdl-2.30.so -l:libz.so.1 -l:libc-2.30.so -l:libgcc_s.so.1 -o "$out/$test"
done
replay() {
    qemu-arm -cpu cortex-a7 -L build/sysroot -E LD_LIBRARY_PATH=build/sysroot/lib "$@"
}
check() {
    id=$1
    case_dir="build/fivegame-kernel-private-v2/cases/$id"
    case "$id" in
        003) cold=8656; verify_mode=cold-off; pair_mode=both-cold-off-toggle ;;
        *) cold=0; verify_mode=full; pair_mode=full-toggle ;;
    esac
    replay "$out/replay" "$out/candidate.so" "$case_dir" "$cold" "$verify_mode" verify >"$out/$id-verify.log"
    replay "$out/pair" "$out/control.so" "$out/candidate.so" "$case_dir" "$cold" "$pair_mode" >"$out/$id-time.log"
    tail -2 "$out/$id-verify.log"
}
pids=''
for id do
    (check "$id") &
    pids="$pids $!"
done
failed=0
for pid in $pids; do wait "$pid" || failed=1; done
test "$failed" -eq 0
if [ "${D35_CHECK_HELDOUT:-}" = 1 ]; then
    fixtures=build/fivegame-kernel-private-v2/cases/003
    for arm in control candidate; do
        control=''
        if [ "$arm" = control ]; then control=1; fi
        for fixture in canonical heldout; do
            heldout=''
            if [ "$fixture" = heldout ]; then heldout=1; fi
            (
                unset D35_AUDIT_CONTROL D35_AUDIT_HELDOUT
                export D35_AUDIT_STATE=1
                if [ -n "$control" ]; then export D35_AUDIT_CONTROL=1; fi
                if [ -n "$heldout" ]; then export D35_AUDIT_HELDOUT=1; fi
                replay "$out/replay" "$out/candidate.so" "$fixtures" 8656 cold-poison verify \
                    >"$out/$fixture-$arm.log"
                sed -n '/^audit_/p; /^callback_layout=/p' "$out/$fixture-$arm.log" >"$out/$fixture-$arm.identity"
            ) &
            pids_heldout="${pids_heldout:-} $!"
        done
    done
    for pid in $pids_heldout; do wait "$pid" || failed=1; done
    test "$failed" -eq 0
    cmp "$out/canonical-control.identity" "$out/canonical-candidate.identity"
    cmp "$out/heldout-control.identity" "$out/heldout-candidate.identity"
    test "$(wc -l <"$out/canonical-candidate.identity")" -eq 42
    test "$(wc -l <"$out/heldout-candidate.identity")" -eq 1242
    printf '%s\n' 'PASS canonical and held-out Star Fox pixels, PCM, two reloads, normalized state and callback boundaries'
fi
