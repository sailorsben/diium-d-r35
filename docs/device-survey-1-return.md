# Survey1 return and storage repair — 2026-10-09

The collector ran, but its evidence did not survive completely. Private return:
`device-evidence/snes-mvp-return-20261009T180632Z`; preservation/repair:
`device-evidence/survey-return-20261009T180632Z`.

| Observation | Result |
|---|---|
| Marker | Correct run ID consumed; wrapper exit0 |
| Collector | 1,984 jobs; 4,045,023 reported bytes; 11.065 seconds |
| Returned captures | 329 present of901 reported; 572 absent after capture0674 |
| Missing nonempty / empty captures | 521 /51 |
| Other read failure | `/proc/mounts` is a refused symlink; use `/proc/1/mounts` |
| Read-only FAT check | Exit3; trailing entries in `retro/device-survey/results`; 17,856 KB lost allocation |
| Approved repair | 521 chains preserved as files; exit1; subsequent CHKDSK exit0 |
| Preservation | All789 previously readable files unchanged; all1,310 post-repair files archived and verified |

The521 missing nonempty captures require exactly17,856 KB when rounded to the
card's32 KiB allocation units. Both count and space match the recovered chains.
Ben confirms stock ROM deletion happened before survey installation; read-only
CHKDSK passed immediately after installation. The old ROM deletion therefore
does not explain this new survey-directory damage. Individual recovered chains
are preserved privately; their original source names are not guessed.

The report claims completion although later capture directory entries are lost.
This is consistent with a FAT directory-growth/persistence failure. The exact
driver, media, write ordering and shutdown cause remain unproved. Fsync and
successful process exit did not establish physical persistence. Ben used the
physical power switch/button, the only shutdown control; there is no launcher
shutdown option. Whether that control performs orderly filesystem shutdown is
unverified. Testing must support this normal device path, not require a nonexistent menu.
The captured stock `/power_key` helper (SHA256
`a754c50d9843eb94e163424988b86a313a642899441a7847aa3e60b393ac12eb`)
calls `system("poweroff")` at0x10664 after GPIO operations. This establishes a
software shutdown request, not an immediate hard cut or completed FAT unmount.

Strict51-MVP/49-lab collection completed. Compared with the preinstall archive,
only init contains the intended survey hook; saves, snapshots, runtime and lab
content match. The return command restored exact init **before** the fresh FAT
check exposed damage. That ordering was a manager gap: restoration now archives
first and refuses writes on an unhealthy volume. A consumed hook already boots
stock and does not require immediate restoration on a damaged card.

## Surviving platform discoveries

- SPI0.0 is bound to spidev. Its DT node is
  `/soc/spi@C0090000/nor-flash@0`, chip select0, maximum20 MHz, receive bus width2.
  This is a declared NOR-flash candidate, not a measured chip ID or capacity.
- USB device controller `gp,gpa7xxxa-usbd` atD1100000 is declared enabled;
  D2800000 is disabled. `/sys/class/udc` and gadget config directory are absent.
  These facts do not qualify a USB recovery mode or rule out a bootloader mode.
- Boot/NAND helper and module copies survive and were reviewed offline without
  execution. Their existence does not prove a registered NAND storage interface.
- The privately backed-up `vrtemu` contains an actual SD-to-SPI updater.
  [Recovered contract](firmware-update-contract.md) separates code from strings.

## Correction and next physical run

Survey2 stores captures in one indexed `captures.bin` plus `report.jsonl`.
Each range has CRC32; return analysis also checks lengths, contiguity and the
completion byte count. Both directory entries are synced before capture growth.
Native and actual ARM fixtures collect600 independent DT properties into just
two result files. Corrupted/truncated bundle, missing v1 files, deadline/reap,
sparse device shell and unhealthy restoration checks pass:21 software checks.
These checks do not establish that this FAT/media/driver fault is fixed physically.

After repair, prior results and all521 recovered files were archived before
rearm. Survey2 run ID `8fc1bcb371894ef0a4b7e75bdc52909d` was armed on D:;
baseline `device-evidence/snes-mvp-return-20261009T182253Z`. Independent readback
verifies release/init/marker and972 unrelated card files, including recovered
chains. Postinstall CHKDSK passes. No other test is armed.

That [physical return](device-survey-2-return.md) now verifies all905 ranges and
clean FAT; exact init was restored after a fresh health check. The next separate
[SPI identification probe](spi-identify.md) is armed. Internal splash replacement
and the audio fix remain pending. Archive and check FAT **before any card mutation**.
