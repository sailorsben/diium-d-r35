# Internal UART firmware correction — 2026-10-16

The user authorized preparing, qualifying and arming I: for an internal firmware
update. This moves the exact physically used UART module and finite boot helper
into the internal rootfs. It does not require card payloads to apply the fix.
Both the first static Vesper screen and current Wings2 animation stay exact.
Physical flash, early attachment and normal boot acceptance remain pending.

## Firmware and startup contract

Baseline is the expected programmed Wings2 image, SHA256
`5c2f34e6b4451b27fa5e6782f1396d8e6a3bf485e24c0fe209b44854f77660c3`.
The user reported that update successful; a complete post-Wings2 SPI readback
was not collected. The earlier full static-screen image has two matching
physical reads. Keep those evidence boundaries distinct.

Only existing rootfs file `init.project.rc` changes. After device setup and SD
mount selection, before either card init or the internal stock fallback, it
synchronously invokes `/d35-uart/launch.sh start`. Four new cpio entries contain
that directory, wrapper, existing module and existing helper. All other original
cpio records, including duplicate directories, retain contents and metadata.
Boot instructions, static bitmap, kernel, device tree and showlogo are exact.
The gzip is 3,388,469 bytes in a 3,406,558-byte slot: 18,089 bytes spare.

| Artifact | SHA256 |
| --- | --- |
| Candidate before vendor metadata | `fd775904a792e7a8d0bad63509dec0891c406de6932a0ef909b2f46f7ab2165d` |
| Expected programmed image | `8d0266046f5acf3f82e117447e653ee4e5c68fe70889f15af32936c8a18264d2` |
| WQW/ZIP update, 5,804,499 bytes | `ed9cd16d43fc2dde0c7792b3dbe32f53b15180804669c56f300697b8d2639425` |
| Unchanged UART module | `009d1a2e726668361b0b41b0fc358f02ba3c9cf08ba1712a690c0f312cf1a1b4` |
| Unchanged finite helper | `1d00fa00e3e0815ce8c30cf08132f4f1ee085f7df9a65bb56d542fc3f13731e2` |

The helper retains exact-kernel guards, safe refusal, restoration/drain and
uncertain-ownership barriers. Successful firmware attachment writes a RAM-only
identity receipt. The card wrapper is updated to verify that receipt plus active,
uncapped, fault-free status and avoid loading a second owner. If firmware safely
retains the original handler, the existing card fallback remains available.
Uncertain ownership/status withholds stock startup. A powered-off card's existing
`retro/uart-fix1/disabled` switch bypasses both boot hooks. The original normal SD
init, UART module/helper, stock binaries, saves and prior evidence stay exact.

## Qualification

35 offline checks pass: GNU gzip; independent libarchive extraction of init,
module, helper, wrapper and logo; exact Thumb bitmap/loader execution for baseline
and candidate; actual captured ARM vendor updater acceptance and four refusal
cases; original logo ZIP decoding/all 18 sprite frames; exact firmware BusyBox
startup/owner/fallback/bypass/fault barriers for card and internal stock paths.
The unchanged module/helper retain their hash-verified 18-module-group and
16-helper-case qualification and prior physical card-boot evidence.

The updater simulation erases 20 blocks and programs 5,120 pages against RAM,
including metadata block 0, and matches the expected programmed bytes. This is
not physical flash or external recovery qualification. The firmware adds no
userspace daemon or per-IRQ storage logging. Actual internal early attachment
must still be verified on the physical return.

Eight temporary-card staging cases cover success, both write-phase failures,
both post-write filesystem failures, existing update, competing armed test and
changed-hook refusal. Failures restore the exact old card wrapper and remove
only the newly owned trigger after a health gate. Existing saves/evidence remain
exact. Raw images, updater bytes and fixtures stay private and ignored.

## Staging and physical update

Fresh sparse archive: `a7-pair-before-20261017T005453563011Z`. It hashes every
existing file and retains zero new content bytes. No full backup is made; the
existing recovery artifacts remain in place. The staging gate requires clean
pushed source, exact qualified artifacts, clean FAT, exact card/init/UART/vendor
hashes and no armed tests or update. Only `retro/uart-fix1/launch.sh` changes;
only `retro/update/Code.bkp` is added. A separate verifier rehashes all existing
files, checks the full ZIP CRC/image and exact file set, and checks FAT again.

**STAGED AND INDEPENDENTLY VERIFIED ON I:** exact source `726f89c` was pushed
before arming. All 10,824 protected existing files, the authorized wrapper
change, complete update ZIP/CRC/image and exact file set verify. FAT is clean;
no emulator test is armed. No full backup or additional saved content was made.
[Installation receipt](../evidence/2026-10-16/uart-firmware1/installation.json) ·
[Independent readback](../evidence/2026-10-16/uart-firmware1/live-verification.json).
Physical flashing, rootfs boot and early UART attachment remain pending.

Safely eject I:, insert with the handheld powered off and sufficient battery,
then boot normally. Allow the vendor update to finish without interrupting power
or removing the card. If it powers off at completion, turn it on once more.
Confirm Vesper static screen -> Wings2 animation -> stock launcher, then power
off normally and reconnect I:. No emulator test is armed. Collect before changes;
remove only the exact known update trigger after healthy-FAT/hash verification.
Do not automatically retry a failed update. Full firmware readback and UART
attachment verification are the next acceptance steps. External recovery remains
unqualified, as in the prior authorized firmware updates.

Public [preparation](../evidence/2026-10-16/uart-firmware1/preparation.json) and
[qualification](../evidence/2026-10-16/uart-firmware1/qualification.json) contain
hashes and evidence boundaries, never private firmware contents.
