# Stock ADC and low-battery trace — 2026-10-16

**Finding:** stock software contains a concrete false-low path. Each sample opens
a fresh ADC client whose saved value starts at zero. Failure to acquire the ADC
semaphore returns that zero plus `0x8000`; the frontend discards the flag, classifies
zero as critical battery, stops sampling, and can request poweroff. Both GPIO
checks being nonzero overrides the classification to state 5, which could mask
this while externally powered. The electrical meanings of these pins are not yet
verified. **We have not observed the timeout or a failed ADC read on this device.**
This is a falsifiable explanation for the symptom, not a confirmed diagnosis of
the battery, charging circuit, or why the symptom began after the UART flash.

The user reports completing the pre-kernel rollback and still seeing the warning.
The latest sparse return hashes 1,601 files and adds only 18,937 content bytes.
Only `retro/swapfile` differs from the post-cleanup expected inventory. There is
no fresh raw ADC/error/GPIO trace or whole-SPI readback establishing this boot's
exact firmware. Deterministic UART boot-log bytes cannot independently date it.
No new full backup, firmware flash, threshold adjustment, or diagnostic arming.

## Actual production path

The SD init launches `retro/main`, which forks and executes a sibling `vrtemu`.
The active SD `vrtemu` is 1,660,140 bytes, SHA256
`8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72`.
Its heartbeat is `xintiao` at `0x13fd4`. The internal `/system/bin/vrtemu` is a
different, 113,184-byte fallback and is insufficient evidence for the SD UI.
Initial fallback analysis was superseded by the exact SD trace and execution.

The SD binary derives its work directory from its executable path and loads
`adcset.ini` on the first heartbeat, using `r+b`. The actual card file is exactly
`318,310,300,290,275\r\n`, SHA256
`842e7cb861c6ce2faea7182f22236cb9ac26b34ac7f51e75f79702e47976343f`.
Both this configuration and the SD executable match the archived inventory from
before the direct-kernel UART flash. The rootfs fallback configuration is instead
`315,310,290,285,280`; it is not the active SD calibration.

Every 128 heartbeat calls, while `ADC_LEVEL >= 0`, the SD code does:

1. Open `/dev/adc` read-only. An open failure prints a message but continues.
2. Select channel 2 with `ioctl(fd, 0x40044701, 2)`, ignoring the return value.
3. Request four bytes with `read(fd, buffer, 4)`, ignoring its return value.
4. Compute `scaled = ((word & 0x3ff) * 330) >> 10`.
5. Classify the sample using the card thresholds and previous-state hysteresis.
6. Read GPIO `0x20b`; if nonzero, read `0x20e`. Both nonzero forces state 5.
7. Close the ADC client. The next sample opens another fresh one.

The GPIO helper issues `0x800c4701` with a 12-byte `{pin,0,0}` packet and returns
the third word on success. Failure is treated as zero, so a GPIO failure also
removes the state-5 override. No GPIO failure was physically observed.

Ignoring transition hysteresis, the bands are:

| Scaled ADC units | State | Behavior |
|---|---:|---|
| >318 | 0 | Highest ordinary battery state |
| 311–318 | 1 | Ordinary state |
| 301–310 | 2 | Ordinary state |
| 291–300 | 3 | Ordinary state |
| 276–290 | 4 | Blinking low icon |
| ≤275 | -1 | Critical, subject to startup/HDMI/GPIO rules |

These are vendor ADC units, not calibrated battery voltage or percent. Critical
is raw ten-bit ADC ≤856. Startup suppresses critical at heartbeat 128; heartbeat
256 can set it. HDMI suppresses critical too. A negative state returns before
the next ADC or GPIO read, so the frontend cannot recover by observing a later
healthy sample or reconnection within that process.

## Exact driver mechanism

The preserved rootfs ADC module is `gp_adc_module.ko`, SHA256
`d34ddc39546399759d374e60f4a523ddd5a388412ee6a94c9e95feddf4ab46d5`.
It belongs to the unchanged rootfs in the qualified pre/post-UART images.

- `gp_adc_fops_open` (`0x324`) calls `gp_adc_request` for per-file client state.
- `gp_adc_request` (`0x178`) explicitly writes zero to client offset 12, the
  saved sample, at `0x1bc`.
- `gp_adc_read` (`0xa0`) waits up to 30 jiffies for the ADC semaphore. Failure
  branches to `0x148`, logs `adc read time out, return last value channel=%d`,
  and returns `saved_value + 0x8000` at `0x158–0x15c`.
- The first conversion on a fresh handle therefore returns **`0x8000` on that
  semaphore timeout**, even if the battery itself is healthy.
- `gp_adc_fops_read` (`0x258`) copies two bytes for any nonnegative result and
  returns 2. The frontend's request for four bytes is not itself a failed read:
  this two-byte return is the driver's contract, and the ten-bit mask discards
  untouched upper bytes. The bug is ignoring status and the timeout flag.

The normal conversion path also ignores `down_interruptible`'s return. A genuine
negative read leaves the frontend's stack buffer untouched; exact ARM execution
reproduces a critical result after a prior zero sample followed by read failure.
That fixture demonstrates possibility, not the live stack contents or actual
occurrence on this device.

## Warning and shutdown consumers

The actual SD menu `mui_WaitNMI` (`0x836b4`) checks `ADC_LEVEL < 0`, loads
`warning.zip` / `poweroff.raw`, displays 640×480 RGB565, waits five seconds,
turns the backlight off and invokes `system("poweroff")`. The exact path executes
in QEMU with all display/power operations intercepted and checked.

Gameplay's `Load_Proc2` (`0xa426c`) independently checks the same global and
contains the same warning, five-second delay and `poweroff` request, plus its
LED/sound-level and conditional GPIO shutdown handling. This gameplay branch is
disassembled, not executed by the harness. Software can therefore cause an
apparent battery shutdown without proving that the cell voltage collapsed.

## Qualification and evidence boundary

[Qualification](../evidence/2026-10-16/stock-battery-trace/qualification.json) and
[execution](../evidence/2026-10-16/stock-battery-trace/execution.txt) pin the vendor
hashes, exercise the exact SD ARM heartbeat over 49,152 raw/timeout-flag/previous-
state/GPIO combinations, verify the actual config path/parser, startup and HDMI
rules, ignored open/start/read failures, negative-state latch and menu poweroff.
The independent hysteresis model initially missed state 1's upper two-unit
margin; disassembly corrected it before the exhaustive test passed. Config open
mode was measured as `r+b`, not assumed read-only. No helper result establishes
physical charge state or a timeout's occurrence.

The next discriminating physical observation is a passive trace of the **stock
frontend's existing calls**, through plugged-in → unplugged operation: ADC open
and channel-start result/errno, read result, raw 16 bits including `0x8000`, scaled
value, both GPIO ioctl results/values, and classification. Do not add a competing
ADC poller or lower thresholds. A timeout flag/failed read preceding critical
would implicate error handling; successful unflagged readings ≤856 would shift
the inquiry to the analog reading, reference/divider, charging path or cell.
No such diagnostic has been installed or armed in this turn.

## Preservation and update disarming

Return evidence was archived before any card change using `sparse-attempt-v1`.
The only planned card mutation is removing the exact already-used
`retro/update/Code.bkp`, after host-package verification, retained-evidence
readback, clean FAT and complete file/hash checks. Recheck the exact remaining
file set and hashes and clean FAT afterward. Preserve the card UART init/module/
wrapper, ADC config, stock executables, every save and all evidence. This prevents
an unintended repeat update; it does not flash or repair anything.

The [card preservation receipt](../evidence/2026-10-16/stock-battery-trace/card-preservation.json)
is authoritative for completion of trigger removal. Original rollback package
remains on the host in the existing rollback slot. No additional full backup.
