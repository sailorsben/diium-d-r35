# Full SPI readback and boot-image inspection — 2026-10-09

Run `5250ec9cd87740ff9fba5ec82ae3a707` completed both independent8MiB reads
in103.771059 seconds. Ben returned the card after about ten minutes. All4,111
messages completed, three identity phases each returned `c84017c84017`, status
remained00, and there was no timeout, competing owner or pending child reap.
The consumed marker matches; the wrapper reports `readback_exit=0`.

Both complete passes are byte-identical, CRC32 `3743368c`, SHA256
`5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b`.
The returned16MiB bundle is also verified independently on Windows. This
qualifies full nominal-range readback for this run. No flash or global SPI
configuration writes occurred. It does not qualify programming or recovery.
[Analysis](../evidence/2026-10-09/spi-readback-return/analysis.json).

## Preservation and normal startup

Archive first: `device-evidence/snes-mvp-return-20261010T003708Z`.
Fresh read-only CHKDSK finds no problems. All51 MVP/progress files match the
preinstall baseline except the intended init hook;49 lab and43 prior-profile
files match exactly. Production and reader-release hashes are unchanged.
**No FAT repair is needed.**

Restoration archived again in `snes-mvp-return-20261010T003804Z`, checked fresh
health/consumed identity and restored the exact init SHA256
`b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7`.
Independent post-restoration readback verifies protected progress, prior profiles
and the full capture; nothing is armed and post-restoration FAT remains healthy.
The UTC archive dates are October10; the local America/Chicago date is October9.
[Preservation](../evidence/2026-10-09/spi-readback-return/preservation.json),
[restoration/readback](../evidence/2026-10-09/spi-readback-return/postrestore.json).

## The second animation is located

Exact private image inspection finds a section table at flash0x0c0000:

| Table name | Flash offset | Stored bytes | Verified payload |
|---|---|---:|---|
| kernel | 0x0c0078 | 2,366,616 | ARM zImage magic; embedded gzip expands to7,476,028 bytes |
| initrd | 0x301d10 | 3,406,558 | One CRC-valid gzip member;8,455,680-byte cpio newc rootfs |
| cmdline | 0x6417ee | 10,490 | Flattened device tree; header total size matches table |

The table's offsets and lengths agree with complete gzip boundaries and the
device-tree header. This is extracted image structure, not proof of every
bootloader validation rule. The rootfs has559 records including its trailer;
the vendor repeats five directory names, which must remain in their original
order. Treating every duplicate directory as corruption was too strict; repeated
non-directory entries are still refused by the inspector.

Its `showlogo` is198,408 bytes and has exact stock SHA256
`436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b`.
The extracted `init.project.rc` matches the previous runtime capture and starts
`/showlogo &` before SD init. The power-key and watchdog executables also match
their previously captured hashes. This ties the original second animation to
this particular SPI rootfs; it is no longer just an inferred storage location.

## Private replacement prepared, not installed

`build/inspect-spi-boot.py` requires the exact verified flash SHA and extracts
only into ignored `device-evidence`. It replaces the embedded ZIP in rootfs
`showlogo` with the already qualified Vesper ZIP. The resulting executable has
the physically accepted SD-stage SHA
`ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe`.
All8,455,680 cpio bytes outside that ZIP span remain exact: entry headers, modes,
timestamps, directories, device records, links, other files and padding.

The recompressed candidate is3,297,826 bytes,108,732 bytes smaller than the
existing initrd allocation. This establishes that the replacement fits; it is
**not an installable firmware package**. No full modified flash image or
`Code.bkp` is created, and no update is staged on the card.

Six checks pass. Independent Windows libarchive/tar lists558 non-trailer records
and extracts both exact showlogo hashes. Independent GNU gzip verifies and
expands the candidate to the expected complete cpio hash. Damaged archives,
unsafe names, bad CRC, oversized decompression and public vendor-output paths
are refused. [Inspection metadata](../evidence/2026-10-09/spi-readback-return/boot-inspection.json),
[qualification](../evidence/2026-10-09/spi-readback-return/boot-inspection-qualification.json).

Private candidate directory:
`device-evidence/snes-mvp-return-20261010T003708Z/spi-readback/boot-inspection/`.
The source inspector and checks are public; flash, cpio and vendor executables
remain private. Do not publish or copy these candidate files into an update path.

## First screen and remaining constraints

A640×480 little-endian RGB565 span at flash0x8854 decodes visually to the static
orange/blue handheld logo and `D-R35 Plus` text. Its614,400 bytes end at0x9e854,
before further boot-loader strings. The preview is private in
`spi-readback/offline-review/static-splash-preview.png`. This locates a matching
raw bitmap; its boot-loader reference and display contract remain unverified.
The asset text alone does not identify a different hardware model.

The kernel's decoded built-in cpio at uncompressed offset0x61f894 contains only
`dev`, `dev/console`, `root` and `TRAILER!!!`; no rescue init or SD hook is present
in that archive. A verified backup therefore still does not supply recovery from
an unusable external rootfs. USB boot-ROM entry or external programmer recovery
is unqualified. Flash data marked `GPDA` at0x650000 is also uninterpreted.

Next inspect the boot-loader's consumption of the table, image checks and exact
vendor updater container/compatibility checks; retain bootstrap, kernel, DT and
uninterpreted data unchanged. Establish recovery before a persistent write.
Linux4.19's [initramfs unpacker](https://raw.githubusercontent.com/torvalds/linux/v4.19/init/initramfs.c)
accepts NUL padding between archive/compression members. That upstream behavior
alone does not qualify this vendor kernel, boot loader or a padded candidate.
Original-screen replacement and MVP1.18 audio remain unresolved.
