# SD attempt evidence policy — 2026-10-16

Routine I: attempts do not make full-card or full-retro backups. This supersedes
historical instructions to copy every card file before each attempt.

`build/archive-a7-pair-card.py` inventories retro paths, sizes and SHA256s.
`build/archive-presentation-extra.py` does the same outside retro. Static
configuration, launchers, executables, cores, ROMs, swapfiles and frozen test
fixtures are hash-only. Progress (including backup save generations), logs,
results and captures retain content. Unknown static files default to hash-only.
New diagnostic/progress formats must be added to `build/attempt_archive.py`.

Saved content lives once per SHA256 in private
`device-evidence/attempt-objects/`. Attempt paths hard-link to those verified
objects. An unchanged retry adds manifests and directory entries, zero duplicate
content bytes. Changed progress/logs add only their new content; older generations
remain recoverable. These are immutable evidence files: never edit retained
payloads in place. Create new analysis outputs, or unlink an existing output
before replacing it. Keep the object store when cleaning up individual attempts.
Hard-link failure aborts; there is no fallback to full copying.

Manifests declare `schema=sparse-attempt-v1`, `stored` per file, and
`new_content_bytes`. `all_retro_files` remains the complete hash inventory for
protected-file checks, not a claim that all those bytes were copied. Collection
errors abort without a successful manifest. The existing read-only FAT check,
card identity guard, consumed-marker checks and zero-card-write contract remain.
The first sparse collection saves each selected content hash once; it does not
trust the old inventories whose payloads were deleted during cleanup.

The current FFVI installer verifies static inventory hashes against the card,
and saved content against the host archive. Its reporter verifies returned
payload hashes from the inventory and uses the hash-matched local frozen package
for static plan data. It still reads raw physical logs from the returned archive.
Older historical analyzers that require a full copied package need migration
before reuse; do not restore bulk backups to satisfy them. Source changes also
invalidate previous source-pinned qualification receipts; requalify before the
next installation. This change does not install or arm anything.

Keep the original recovery backups separately. A sparse attempt archive is
evidence and saved progress, not a full-card recovery image. Full backups are a
separate explicitly requested operation, not part of routine attempt collection.

Validation: `python build/check-attempt-archive.py` exercises a fake card with
progress changes, unchanged retries, logs/results, outside-retro saves, static
hash-only entries, fixture exclusions, corrupt content and hard-link refusal.
The fixture verifies the source card stays byte-identical during collection.

## Retired card profiles and plain-text diagnostic retention

Direct diagnostic run/pass/epoch .txt/.json outputs and named root reports such
as pcm-full.txt are retained sparsely even outside results/logs. Fixtures still
remain hash-only. The previous gap and verified recovery are documented in
[card test cleanup](card-test-cleanup.md). Hash-only inventory alone is never
proof sufficient to delete unique card evidence. Retired package deletion needs
an actual verified host byte copy for each removed file. Preserve all save/state
paths and leave unmatched static files in place; no full-copy fallback.
