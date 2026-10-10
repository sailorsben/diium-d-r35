# Vesper original-animation SD update — 2026-10-09

The subsequent [first static Vesper screen](vesper-static-firmware-update.md)
is staged for the next SD boot. The evidence below records the completed
second-animation update and its removed trigger.

**Verified second-animation state - 2026-10-10:** both complete8MiB reads match the
expected installed Vesper image byte-for-byte. Normal SD init is restored,
Code.bkp is absent, no test is armed and the final FAT check passes. The user's
accepted boot remains static D-R35 -> Vesper -> default launcher. First static
screen stays; external write recovery is unqualified and MVP1.18 audio unresolved.
[Complete verification and restoration](vesper-flash-verification.md).

The checkpoints below preserve their original evidence boundaries; the verified
return above supersedes all pending return/readback instructions. Do not reflash.

**Physical boot accepted:** after normal manual power-on, the user reports
static D-R35 -> Vesper replacing the regular D-R35 animation -> default launcher.
This is the requested original second-splash replacement, with the first static
screen preserved. No repeat update was reported. Boot/animation acceptance is
based on the user's physical observation, not a collected photograph/video or
full SPI readback. The card has not returned; update-trigger removal, exact full
flash comparison and another cold boot without the trigger remain pending.

That acceptance checkpoint's next action was card return and trigger removal;
both are now complete. Do not reflash.

**First physical report:** battery-only startup reached100% progress, then the
device powered off; USB charging was not connected and no automatic restart was
observed. Normal manual power-on once with the SD inserted was the next
step and has now succeeded. The conservative ten-minute instruction below applies to an active or
uncertain update, not waiting for writes in an actually powered-off device.
Exact completion re-inspection confirms successful programming return -> sync
at0x13990 -> reboot(0x01234567) at0x1399c. The report fits that path but is not
proof of actual flash equality, new firmware boot or the replacement animation.
No postupdate logs/readback collected yet.

The exact qualified update was **staged on D:**. Replacement-animation boot
acceptance now passes; exact physical flash readback remains pending. The user explicitly chose to proceed
through the SD updater before obtaining external recovery equipment, accepting
that a failed boot could require purchasing a programmer and restoring the chip.
This supersedes the earlier wait-for-equipment execution gate. Recovery is still
unqualified; the vendor still erases boot-code block0.

## Staging result

Run `c157689a17174f2c8e433c9ce58c0c68`, staged2026-10-10T04:42:48Z
(October9 America/Chicago). Private preservation archive:
`device-evidence/snes-mvp-return-20261010T044231Z/`.

Archive51 MVP/progress files,49 lab files, prior survey/splash/identification/
readback profiles and current root/display logs before changing the card.
Retain another exact full SPI backup and the package privately. Fresh pre/post
staging FAT reports pass. Compare997 readable card files before/after; every
original file stays byte-identical. Windows-owned `System Volume Information`
is excluded from this inventory. Only `retro/update/Code.bkp` is added.

| Artifact | Bytes / SHA256 |
|---|---|
| SD `retro/update/Code.bkp` | 5683533 / `5263abf58bdfd161e90811e6cc0ecd233657ac8328a924185234c98af2ad8499` |
| Original full SPI backup | 8388608 / `5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b` |
| Candidate before vendor metadata | 8388608 / `246a46afa5cda655b47db787dff94e430bbf7f8a897b751cfca28ddc79f68ff7` |
| Expected programmed image | 8388608 / `d20301be923288e6ace49b43dd8cce306855ded8cd961643e5ee14854d9e6f03` |
| Unchanged SD init | `b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7` |
| Exact SD updater | `8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72` |

The expected programmed image includes the vendor's CRC/time replacements at
0x100/0x104 (`f2914d07`/`5d496000`). A readback equal to the candidate's *unmutated*
SHA is therefore not the expected successful result. No other test is armed.
An independent PowerShell readback confirms package/init/updater hashes.

`build/manage-vesper-firmware.py` validates the exact package,8MiB ZIP member,
CRC, timestamp, original backup and prior nine-outcome/source-hash qualification.
It uses the normal vendor trigger with no new init hook or custom SPI writer.
Its6 host checks exercise exact artifacts, wrong-card refusal, actual temporary
filesystem staging, poststage-health failure rollback, existing-update refusal,
and competing armed-runtime refusal. They do not establish physical flash or
recovery. All image/package contents remain ignored/private.

## Historical first-update instructions

1. Safely eject D:, insert the card with the handheld off, and connect charging
   power with a well-charged battery. Leave that power source connected.
2. Turn it on once. The first boot still starts with the old internal screens;
   the SD application must reach its updater before changing the internal image.
   The vendor success path requests an automatic reboot. Actual duration and
   progress presentation on this unit have not been measured.
3. Leave it untouched for at least10 minutes, including any automatic reboot.
   This is a conservative waiting instruction, not a measured completion bound.
   Do not power off/remove the card/unplug during an active update. If it is still
   showing update activity or stuck afterward, report the screen before cutting
   power; elapsed time alone does not prove the write finished.
4. After it has rebooted and reached a stable launcher, observe the new order:
   unchanged static D-R35, then Vesper animation, then stock launcher. The old
   extra SD-stage Vesper one-shot is consumed and remains unarmed.
5. Once the launcher is stable and no update is active, use the normal power
   button and return D:. Preserve logs/package before removal or any other test.

## Exact card-return resume

Run `python build/manage-vesper-firmware.py collect` first. It archives current
MVP/private progress, lab/prior profiles, root/display logs and update folder
before changes. A package disappearing or staying present is not flash proof.
Then `python build/manage-vesper-firmware.py unstage` archives again, requires
healthy FAT and exact package hash, and removes only the known Code.bkp if it
remains. Never remove a changed/unknown package without inspection. Normal init
stays exact. Removing the trigger does not revert internal firmware.

Next obtain a fresh two-pass on-device SPI readback using the already-qualified
read-only reader before stock vrtemu owns the bus. The old reader profile is
consumed; its fresh-install command refuses that existing directory. Prepare a
guarded archived rearm rather than bypassing its checks or destroying returns.
Compare both8MiB passes byte-for-byte with private `expected-after-vendor.bin`
in the staging archive. Inspect all differences and preserve actual bytes. Cold
boot again after removing the update trigger to establish persistence. Physical
screen/launcher observation and full flash verification are distinct checks.

If it cannot boot, normal SD init may be unreachable. Preserve the original
backup and actual symptoms, obtain the recommended external programmer/clip,
qualify voltage/pin mapping/isolation/read access, and restore/verify the original
image externally. No USB/SD-only rescue is qualified. Equipment ownership or
two reads alone do not establish successful write recovery.

The first static screen and MVP/audio behavior are outside this image change.
The Magitek Bio Blast audio failure remains unresolved.
