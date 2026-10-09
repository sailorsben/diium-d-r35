# Device survey2 physical return — 2026-10-09

The indexed survey returns intact. Run `8fc1bcb371894ef0a4b7e75bdc52909d`
completed 1,989 jobs in 10.432 seconds and captured 4,046,126 bytes. The return
analyzer verifies all 905 ranges, their CRC32 values, lengths, contiguity and
completion count. No read failed or was truncated; neither cap nor child timeout
was reached. Six expected optional paths are absent. The consumed marker matches
the installation and the wrapper records exit0.

Read-only CHKDSK reports no FAT problems. The 51 MVP/progress files and 49 lab
files match the pre-installation baseline, apart from the deliberately installed
init hook. All results were archived before restoration. A fresh health check
then permitted restoration of exact init SHA256
`b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7`.
Survey2 is consumed and unarmed.

Private return: `device-evidence/snes-mvp-return-20261009T232801Z`.
Private restoration: `device-evidence/snes-mvp-return-20261009T232840Z`.
The return also preserves an offline review of 32 ELF captures without executing
vendor binaries. Raw captures, vendor binaries and private progress remain
excluded from publication. [Curated result](../evidence/2026-10-09/device-survey-2-return/analysis.json).

This is one successful physical return through the normal power button. It
qualifies the two-file survey for this run; it does not establish that every
storage workload or the exact driver/media/shutdown fault is fixed. The button
is the device's sole user shutdown control. No alternate menu shutdown exists.

## New ownership evidence

The process census finds PID521, `vrtemu`, executable `/usr/retro/vrtemu`, with
FD8 pointing to `/dev/spidev0.0`. That character device has major153/minor0.
An identification probe must therefore finish synchronously before the stock
launcher starts. Running it in the background beside stock would compete with
an established SPI owner.

The board declares `Generalplus EMU Board`, compatible with
`generalplus,gpa7xxxa-emu` and `generalplus,gpa7xxxa`. Runtime root is RAM-backed;
the SD's `/dev/sdcardb1` vfat is mounted at `/media/sdcardb1` and `/usr/retro`.
Its `errors=remount-ro` option is not a physical durability guarantee. Device tree
still declares SPI0.0 as NOR flash; no chip ID or capacity has yet been measured.

## Next physical test

The [read-only SPI identification one-shot](spi-identify.md) is installed and
armed separately. It uses fixed status/JEDEC commands, checks competing owners,
and finishes before stock starts. The returned chip ID must be checked against
a datasheet before a full flash readback is designed. Persistent replacement of
the original second splash and the MVP audio failure remain unresolved.
