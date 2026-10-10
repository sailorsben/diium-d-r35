# SPI identification physical return — 2026-10-09

Run `42401fa0056c4cfda90da165e2ad851f` succeeds. All three six-byte responses
are `c84017c84017`; the identifying triplet is `C8 40 17`. The consumed marker
matches the installation, wrapper exit is0, all five messages complete, and
neither timeout nor pending reap is reported. No competing owner is found.
Status before/after is00. Reported mode is1024 (`SPI_RX_DUAL`), eight bits,
default20MHz; the probe requested one data lane at at most1MHz without changing
global settings. No flash or global configuration writes occur.

Private return: `device-evidence/snes-mvp-return-20261010T000105Z`.
Its UTC directory date is October10; the return is October9 in America/Chicago.
Strict51-MVP/progress and49-lab hashes match the installation baseline, apart
from the deliberately installed init hook. Read-only CHKDSK reports no FAT
problems. A fresh check permits exact init restoration in
`device-evidence/snes-mvp-return-20261010T000150Z`. Results stay archived and
on the card, consumed and unarmed.

The ID identifies a GigaDevice64-Mbit SPI NOR family, with nominal capacity
8,388,608 bytes. It does not distinguish every silicon revision or package.
GigaDevice's [GD25Q64E datasheet](https://download.gigadevice.com/Datasheet/DS-00484-GD25Q64E-Rev1.6.pdf)
lists the triplet on printed page19 and ordinary03 reads with a three-byte
address on page22. The primary [Linux4.19 SPI NOR table](https://raw.githubusercontent.com/torvalds/linux/v4.19/drivers/mtd/spi-nor/spi-nor.c)
maps `0xc84017` to `gd25q64`,128 blocks of64KiB. These agree with the exact
vendor's recovered03/24-bit read path. Capacity is derived from that matched
family; a full readable image is not yet verified.

The next [two-pass readback](spi-readback.md) reads the full nominal range
without writing flash. Matching passes are a backup, not proof of recovery or
a safe repacked update. Persistent original-splash replacement and audio remain
unresolved. [Curated result](../evidence/2026-10-09/spi-identify-return/analysis.json).
