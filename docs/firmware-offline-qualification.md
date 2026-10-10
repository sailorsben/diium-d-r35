# Original-animation replacement: offline firmware qualification — 2026-10-09

The exact captured loader accepts both the original image and a private Vesper
candidate in QEMU. The exact vendor updater accepts our WQW/ZIP container,
extracts the complete image, validates compatibility and programs a simulated
RAM flash to the expected bytes. This establishes a concrete image/update path.
It does **not** establish physical flashing or recovery. D: was not changed;
normal init remains restored and nothing is armed. Both original screens remain.

[Interpreted loader contract](../evidence/2026-10-09/firmware-offline-qualification/loader-contract.json),
[candidate preparation](../evidence/2026-10-09/firmware-offline-qualification/preparation.json),
[nine offline outcomes](../evidence/2026-10-09/firmware-offline-qualification/qualification.json).
An expected vendor failure is recorded as an observed fault, not a safe rejection.

## Candidate and loader

Baseline is the two-pass verified8MiB SPI image, SHA256
`5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b`.
Candidate8MiB SHA256
`246a46afa5cda655b47db787dff94e430bbf7f8a897b751cfca28ddc79f68ff7`.
The only intended flash changes are:

- Four-byte initrd length at0xc0040:3406558 becomes3297826.
- Existing rootfs slot at0x301d10: qualified Vesper gzip plus108732 FF tail bytes.

Every byte elsewhere remains exact, including bootstrap/static bitmap, kernel,
device tree, GPAP header and uninterpreted GPDA data. Within the uncompressed
cpio, only the qualified embedded showlogo ZIP differs; all code, archive headers,
other files and duplicate directory records are exact. Earlier independent
libarchive/GNU gzip qualification remains applicable to this same gzip/cpio.

The bootloader entry vectors establish flash+0x200 mapped to RAM0x02600000.
Its section functions are Thumb; ordinary ARM disassembly misreads them.
`build/check-boot-loader.c` loads the exact private code at its original addresses,
intercepts SPI reads and logging, and invokes its actual parser/getter, GPAP
copy selector and three-section loader. It never invokes boot main or the kernel.
QEMU checks both images, rejects wrong section names/short headers, verifies all
three exact reads and checks patched DT `linux,initrd-start/end` values. The
candidate end is0xa00000+3297826. No assumption about compressed-stream padding
is required: the loader receives the actual compressed length.

The separate first screen's code reference is now verified. Thumb instruction
at flash0x54ca stores the bitmap pointer0x02608654 from literal0x5628 to
register0xd05001e0. That pointer resolves to the private bitmap at flash0x8854.
Instruction0x54f6 writes packed640×480 dimensions0x01e00280 to0xd05002e4.
These are distinct stores; the dimension word is not the bitmap pointer.
This candidate preserves that screen. Physical MMIO modification is untested.

GPAP chooses a primary/secondary **header copy** by magic/generation; that is
not evidence of a second full firmware slot or automatic recovery fallback.

## Exact vendor updater

Hash-qualified `vrtemu` is
`8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72`.
`build/check-vendor-updater.c` maps its exact ELF and bundled ZIP routines,
intercepts SPI/device/display/chunk/process-control seams, and invokes
`UpdateROM`/`UpdateROMProc`. Unexpected imports abort. Erase and page-program
callbacks operate only on an8MiB malloc buffer; all ranges, page alignment and
NOR1-to0 semantics are checked. Full simulated readback must equal the image
after the vendor's metadata mutation. The capture callback deliberately returns
failure after the simulation, preventing the vendor sync/reboot success path.
UpdateROM has no stable status return; qualification observes its program seam.

Accepted container: `WQW` followed by a single-member ZIP with an8MiB full SPI
image. Member name `SPI_ROM.bin` works; it is not proven mandatory. On-device
main's established trigger remains executable-directory `update/Code.bkp`,
not the unrelated standalone SPI_ROM.bin path string. The exact ZIP decoder
accepts the three-byte prefix with ZIP-relative offsets from Python's writer.

| Field | Observed rule |
|---|---|
| Flash0x100 | Stored first-item CRC; same CRC skips programming |
| Flash0x104 | Stored ZIP DOS date/time |
| Flash0x108 | Existing compatibility word0x0134d829 |
| Compatibility | Unsigned image word /10 must equal existing word /10 |
| Before programming | Vendor replaces image0x100 with CRC and0x104 with ZIP time |
| This fixture | CRCf2914d07, DOS time5d496000 |

The full-image CRC is computed **before** those metadata words are rewritten;
the flashed image therefore need not have that same whole-image CRC afterward.
All six SPI configuration calls happen before container validation, including
rejected/repeat fixtures. Those calls are also intercepted in QEMU.

The compatible fixture causes55 block erases and14,080256-byte page programs:
block0, table/kernel block0xc0000, and53 rootfs blocks0x300000–0x640000.
**Block0 contains boot code and is erased solely because the vendor rewrites
metadata.** Blocks0xc0000 and0x300000 also contain preserved kernel bytes, so
their complete blocks must survive any erase/rewrite. A rootfs-only intent does
not imply a rootfs-only failure domain when using this updater.

Incompatible-family, matching local/central bad-CRC, missing-prefix and
already-recorded-CRC fixtures produce zero erase/program calls. Inconsistent
local/central CRC fields instead produce a reproducible NULL-image dereference
at ARM0x13920, address0x108, after six configuration calls and before any flash
erase/program. The fault is captured explicitly under QEMU. It is not physical
proof of a device crash, and does not qualify the vendor as a safe arbitrary
package validator. Never use a dummy/malformed update on the handheld.

## Reproduction and private artifacts

Owned tools: `build/extract-spi-loader.py`, `build/prepare-vesper-firmware.py`,
`build/check-vesper-firmware.py`, and the two C harnesses. Inputs are exact-hash
bound by the Python checker. Output is restricted to fresh directories under
ignored `device-evidence`; the checker also exercises public-output refusal.
The checker builds both harnesses with Cortex-A7 ARM, strict warnings and fixed
high executable addresses, then runs the exact seams under QEMU. This is offline
code/format evidence, not on-device input/audio/display or performance evidence.

Private baseline:
`device-evidence/snes-mvp-return-20261010T003708Z/spi-readback/offline-review/spi-nor.bin`.
Qualified private image/packages/reports:
`device-evidence/snes-mvp-return-20261010T003708Z/spi-readback/firmware-qualified-candidate/`.
The preliminary `firmware-candidate/` directory predates the final rejection
suite; use the qualified directory. No image or `.bkp` is installed or published.

Example offline checker invocation from the workspace:

```powershell
python build/check-vesper-firmware.py `
  device-evidence/snes-mvp-return-20261010T003708Z/spi-readback/offline-review/spi-nor.bin `
  device-evidence/survey-return-20261009T180632Z/full-readable-card/files/retro/vrtemu `
  device-evidence/snes-mvp-return-20261010T003708Z/spi-readback/firmware-qualified-candidate
```

## Exact next physical work

Ben reports no SPI programmer available. Subsequent [board photographs](board-identification.md)
confirm VT569B and expose an eight-pin flash package. The MD-marked chip's middle
line appears25Q64CSIG, consistent with the prior JEDECc84017/8MiB evidence.
The matching GD25Q64C manufacturer specification is2.7–3.6V/SOP8 208mil;
MD branding is not authoritatively decoded. Recommend Waveshare CH347 SKU25411
at3.3V and Pomona5250 clip, with jumper leads/multimeter. Real clip contact,
pin mapping, voltages, bus isolation and external read/recovery remain pending.

Use hardware with confirmed target-compatible supply **and SPI signal voltages**.
The [flashrom project's CH341A/B documentation](https://raw.githubusercontent.com/flashrom/flashrom/main/doc/supported_hw/supported_prog/ch341ab.rst)
describes black boards whose socket supply is3.3V while SPI outputs approach5V;
a3.3V socket label alone is insufficient. The recommended CH347 adapter has a
documented interface-level switch; confirm the actual hardware before connection.

The physical sequence is:

1. Obtain the recommended hardware; the board/marking photographs are preserved.
   The case can be reassembled meanwhile. Reopen with battery/USB disconnected.
2. Match exact datasheet/package, programmer signals, pin1 orientation and
   isolated power arrangement. Determine whether clip/header access works;
   inaccessible packages or bus contention may require hardware isolation.
3. Read the entire chip twice through the external path; require8MiB exact
   matching reads and compare to the verified baseline. Resolve every difference
   before writing. This qualifies access/readback, not yet write recovery.
4. Confirm the external rewrite/verify procedure and the preserved original
   backup before performing the first persistent change. Choose the concrete
   write route with that recovery equipment present, then verify complete
   readback and cold boot through both screens and launcher.
5. If boot fails, use the external path to restore the exact baseline and verify
   readback. Record the physical result; an available programmer alone is not
   an already-demonstrated recovery.

No USB boot-ROM mode, recovery key sequence or SD-only rescue path is qualified.
The normal SD init hook depends on a working internal boot/rootfs. Kernel
execution/vendor-kernel gzip unpacking, physical writing, recovery and actual
replacement remain unqualified. MVP1.18 audio remains unresolved.
