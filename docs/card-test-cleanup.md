# Retired test package cleanup — 2026-10-16

User authorizes removing obsolete diagnostic packages on I:, after host archive
verification, preserving saves/unique evidence and leaving the current rollback
armed. No new full card or retro backup. The scope is an explicit list of 34
retired test profiles; stock/root files, games, Tests, libs, normal SNES runtime,
all save/state/snapshot files, current UART boot files, artwork and update trigger
stay protected. Paths outside these profiles cannot be removed.

## Host verification and recovered text logs

Fresh sparse archive `battery-rollback-return-20261017T031941973187Z` hashes all
11,006 files and has clean FAT with zero initial new content bytes. Before any
delete, each proposed removal requires a complete SHA256/size-matched existing
host package or retained evidence copy. Static files are not copied to make a
new package/card backup. One unmatched executable is retained on card.

Audit exposes a collector gap: text output directly under run/pass directories,
including pcm-full.txt, was hash-only rather than retained. Preserve the 2,046
missing text/metadata files into immutable content-addressed objects/hard links,
verify source and saved bytes, and retain their complete path/hash manifest.
This adds 855,408,318 unique evidence bytes, not a full card backup. A first
classification pass safely refuses the unmatched executable; the supplement
retains only diagnostic text/JSON/consumed-marker metadata. Existing supplemental
links are verified on resume. No card writes occur during preservation.

The collector is corrected for diagnostic run/pass/epoch text/JSON and named
root-level diagnostic reports. Frozen fixtures, binaries and configuration remain
hash-only. Four sparse-archive tests pass with real hard-link permission; the
new cases reproduce the missed raw text paths while rejecting fixture/plan text.

## Exact cleanup gate

Qualified plan removes 9,405 files / 1,382,325,388 logical bytes (about 1.29 GiB).
Keep 683 save/state files in place, including conservative retention of old test
checkpoints; leave the unmatched executable. Some retired directories therefore
remain as save-only shells. Remaining expected file count is 1,601. These are
logical file bytes; FAT allocation/free-space changes are measured separately.

Restore only the old test dispatcher to the exact manifest-qualified normal
SNES1.19 wrapper, SHA256
`35b1c32fa5924e33a0f1da47833b6710e53dadc5ebd832a6b998a86236e2cc13`.
This removes its reference to the retired five-game package without arming the
runtime. The current rollback's retro/init and uart-fix1 files stay byte-exact.
The rollback update SHA256 remains
`2b78853155c087cfaf3dab730cabbb2dabc757982626da53ddb04cb9dc7bc389`.

Five exact cleanup seam cases cover success, mismatched file hash, traversal,
foreign profile and save deletion refusal. Before deletion, reverify every host
proof and live card file plus exact file set and FAT. Validate resolved absolute
targets under their explicitly allowed I:/retro profile, refuse reparse paths,
unlink only listed/hash-matched files, then rmdir only empty in-scope directories.
No recursive tree deletion. Record progress; on an error stop with plan and host
proofs retained. Exact prior bytes remain recoverable from these verified copies.

After deletion, verify all retained file hashes, normal wrapper, exact file set,
all save paths, no game markers, rollback still armed and clean FAT. Independent
readback repeats remaining hashes and validates the complete rollback ZIP/CRC/image
and proven UART boot payloads. Do not flash or alter the battery test during this
cleanup. Keep all host archives/object-store generations; no host cleanup is in scope.

**Status: complete and independently verified.** Source `660fa48` was pushed
before execution. All 9,405 planned files were removed; card file count is now
1,601. Logical bytes removed: 1,382,325,388. FAT free space increased by
1,681,129,472 bytes (about 1.57 GiB). All 683 retained save/state paths and every
remaining file hash verify. One unverified static executable remains in place.
The normal SNES wrapper is restored, no game markers exist, and the exact current
rollback package, card UART init/wrapper/module/helper remain unchanged. FAT is
clean after cleanup and independent verification. No new full backup.

[Completion receipt](../evidence/2026-10-16/card-test-cleanup/result.json) and
[independent verification](../evidence/2026-10-16/card-test-cleanup/independent.json).

[Qualification](../evidence/2026-10-16/card-test-cleanup/qualification.json).
The rollback [physical instructions](battery-rollback.md) remain applicable.
