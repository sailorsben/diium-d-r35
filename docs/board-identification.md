# Physical board identification — 2026-10-09

Ben opened this unit and supplied four board/SoC photographs followed by one
flash-chip close-up. All five originals were copied unchanged and independently
SHA256-verified in the ignored private archive
`device-evidence/board-photos-20261010T041604Z/`, with `photo-receipt.json`.
The photographs include unrelated background material and are not publication
artifacts. Only these interpreted hardware findings are published.

## What this unit shows

- The large processor clearly reads **VT569B** in the last SoC close-up. This
  independently confirms the marking on this unit, not just a sibling teardown.
- The larger eight-pin device beside the processor has exposed gull-wing leads,
  four on each side. The smaller device near the battery connector is labelled U8.
  The flash close-up shows the larger device and its pin-one dot.
- Ben's reading of the flash marking is `MD AY2409 / 25064CS16 / UWE917`.
  The middle line visually appears to be **25Q64CSIG**; faint Q/I/G can resemble
  0/1/6. Preserve the user's transcription separately from this interpretation.
  The MD branding and remaining lot text are not authoritatively decoded.
- The earlier physical JEDEC result is **c8 40 17**, and two complete independent
  reads yielded identical **8 MiB** contents. This supports the GigaDevice
  GD25Q64-compatible family; it does not authenticate the MD-marked silicon.

The [GigaDevice GD25Q64C product page](https://www.gigadevice.com/product/flash/spi-nor-flash/gd25q64c)
specifies 64 Mbit and 2.7–3.6 V operation. Its manufacturer-authored
[Rev3.2 datasheet, mirrored by LCSC](https://datasheet.lcsc.com/lcsc/1912111437_GigaDevice-Semicon-Beijing-GD25Q64CSIGR_C395510.pdf)
lists GD25Q64CSIG as SOP8 208 mil on page63. Page65 gives nominal body dimensions
5.23×5.28 mm and lead pitch1.27 mm. Those are the matching part's specification,
not measurements made from this photograph. The visible package is consistent
with it. Use a **3.3 V supply and 3.3 V SPI signals** for the proposed external
access; confirm actual voltage before connecting to the board.

## Recommended recovery equipment

- [Waveshare USB TO UART/I2C/SPI/JTAG, SKU25411](https://www.waveshare.com/product/usb-to-uart-i2c-spi-jtag.htm):
  assembled CH347 adapter with a switch controlling the communication-interface
  level at3.3 V or5 V; select3.3 V. It includes USB and interface cables. This is
  a hardware recommendation, not a demonstrated read/recovery on this unit.
- [Pomona5250 eight-pin SOIC clip](https://www.pomonaelectronics.com/products/test-clips/ic-test-clips/soic-clip-8-pin):
  its [manufacturer datasheet](https://www.pomonaelectronics.com/files/datasheets/d5250-54_5437_1_01.pdf)
  specifies1.27 mm lead pitch and body widths0.150–0.350 inch, covering0.208 inch.
  Check real clearance/contact retention when it arrives.
- Jumper leads to connect the adapter's supplied interface cable to the clip,
  and a multimeter for pin mapping, continuity and supply checks.

The [Waveshare manual](https://www.waveshare.com/wiki/USB_TO_UART/I2C/SPI/JTAG)
identifies SPI mode1/2 and a3.3/5 V level switch. For flashrom, use mode1:
the [upstream CH347 driver](https://raw.githubusercontent.com/flashrom/flashrom/main/programmers/ch347_spi.c)
supports bulk-mode CH347T/F and explicitly lacks HID-mode support. Its supported
clock settings include468.75 kHz and937.5 kHz; begin conservatively below1 MHz.
No programmer, driver or flashing utility was installed or connected here.
The actual external transaction/probing path must be checked before use.

## Resume with hardware present

The case may be reassembled now, with battery/USB disconnected while closing,
speaker wires and ribbons unpinched, and screws snug. Reopen for external access.
No more identification photographs are required for equipment selection.

Before any connection, establish pin-one orientation, correct clip-to-adapter
mapping,3.3 V supply/signals and a single controlled power source. Battery and
handheld USB must be disconnected. The shared board rail and SoC bus ownership
remain untested: a physically accessible clip does not prove in-circuit access;
isolation may be necessary if the board powers up or contends with the reader.

First perform two complete external reads and compare both to the private
8 MiB baseline SHA256
`5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b`.
Resolve every difference before writing. Then establish the concrete external
restore/verify procedure with the equipment present. Follow the full-image and
cold-boot acceptance sequence in [offline qualification](firmware-offline-qualification.md).
The photos qualify identity/package selection only: no external read, write,
restore, firmware installation, USB recovery or audio fix is claimed.
