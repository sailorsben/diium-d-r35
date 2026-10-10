# Internal firmware update evidence — 2026-10-09

Exact privately preserved SD `vrtemu`: SHA256
`8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72`,
1,660,140 bytes. `build/extract-vendor-update.py` rejects another binary and
checks specific ARM instructions and file-backed ELF addresses. It never runs
the vendor program. [Curated result](../evidence/2026-10-09/device-survey-return/updater-contract.json).

Main obtains its executable directory, appends `update/Code.bkp`, and calls
UpdateROM at0x1231c. UpdateROM at0x133fc opens `/dev/spidev0.0`, configures SPI,
reads existing flash metadata and opens that staged file as `r+b`. It checks
the three-byte prefix `WQW`, uses OpenZipU/first-item extraction, compares CRC32
and compares compatibility data with the existing image before the programming
routine. Complete container layout, chip capacity and compatibility fields still
need recovery. The separate `/media/sdcarda1/SPI_ROM.bin` string is present;
it does not establish that filename as this main-path trigger.

| Recovered SPI operation | Contract |
|---|---|
| Ordinary read | Opcode03,24-bit address,4-byte command then receive transfer |
| Status | Opcode05 |
| Write enable | Opcode06 |
| Page program | Opcode02 plus24-bit address |
| Block erase | OpcodeD8 plus24-bit address |
| ioctl layout | 32-byte transfers; requests0x40206b00 /0x40406b00 |

UpdateROMProc at0x130a0 reads/compares64 KiB blocks, erases differing blocks,
programs256-byte chunks and rereads/retries. A successful update calls sync and
reboot. This establishes a vendor self-update implementation, not physical
qualification of its safeguards or permission to stage a dummy update file.

The two-transfer read layout agrees with the primary
[Linux spidev API](https://kernel.org/doc/html/v5.12/spi/spidev.html): a composite
SPI_IOC_MESSAGE preserves chip select across its transfers. That documentation
also warns that a nonexistent SPI slave need not produce an I/O error. A positive
ioctl alone cannot establish chip identity or successful flash readback.

The survey independently finds the DT NOR-flash node on SPI0.0 and stock vrtemu
holding that node. The [physical identification](spi-identify-return.md) now
returns `C8 40 17` three times: GigaDevice64-Mbit NOR family, nominal8MiB from
matched manufacturer/kernel references. Exact suffix/package and firmware layout
remain unverified. The [two-pass reader](spi-readback.md) is armed synchronously
before stock starts, with fixed03/24-bit reads and byte comparison. Physical
full-range readback remains pending. No SPI program/erase or configuration writes
have been attempted. Capacity is no longer inferred from a sibling handheld.

A flash dump is a backup. Recovery also requires a verified way to rewrite the
chip when normal boot fails. Our SD init hook depends on working internal boot
code, so it does not make a corrupt bootloader recoverable. USB boot-ROM mode,
external programmer access and a complete recoverable image remain unverified.

SD contains replaceable applications/cores, while captured internal init starts
RAM-rootfs `/showlogo` before SD init. The SD application path supports SNES work;
replacing the original second animation needs a persistent internal-image change.
The qualified Vesper SD-stage animation is physically accepted after both stock
screens. Neither original screen has been replaced.
