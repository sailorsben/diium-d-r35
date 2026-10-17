# Kernel-UART five-game return and battery regression — 2026-10-16

The plugged-in run repeats the previous boundary: Mario, Metroid and F-Zero each
complete their first 1,200-call blocking window. F-Zero is not the executing game
when the user presses Start+Select: Star Fox's silent cold replay is active, with
the previous picture retained. It lasts 102.973830 seconds before abort, records
zero measured calls and opens no native PCM. The replay call count is not logged.
This cannot distinguish slow forward progress from a stall. Do not dismiss the
reported freeze as normal replay, and do not call the recorded abort a crash.

The child exits normally with status5; supervisor reaped=1, forced=0, raw1280.
Audio joins, display is idle, board closes and wrapper lab_exit=5 permits stock.
Ranger and every candidate-policy window are not started: zero matched pairs.
This does not qualify the emulator or all five games as fixed. All three complete
windows retain exact render/PCM accounting, full valid histories, no skips/errors,
and valid CPU prefixes. Their conservative 20% headroom gate remains NOT_MET.

| Blocking window | Calls | Minimum sampled reserve | Result |
| --- | ---: | ---: | --- |
| Mario PAL | 1,200 | 2,312 frames / 52.43 ms | Clean bounded window |
| Metroid | 1,200 | 2,199 frames / 49.86 ms | Clean bounded window |
| F-Zero | 1,200 | 2,184 frames / 49.52 ms | Clean bounded window |
| Star Fox | 0 | Native PCM not opened | Cold replay aborted |
| Ranger | 0 | Not sampled | Not started |

Star Fox's retained PCM/input buffers are excluded because pre-measurement failure
can preserve the preceding epoch's buffers. Fresh payload hashes bind all scenes,
inputs, core/controller, markers and normal init to the installed profile.

## Preservation and UART

Archive `uart-kernel-return-20261017T030311712597Z`: 11,005 files hashed,
6,049,004 new sparse content bytes, clean FAT, zero card writes, no full backup.
10,903 of 10,906 pre-install files remain exact. Only authorized dispatcher,
consumed launcher marker and normal swapfile differ. All saves, prior evidence,
old profiles, normal init and stock binaries remain exact. Both test markers
are consumed, no armed tests or firmware trigger; subsequent boot is stock.
No cleanup, rearm, firmware update or rollback was performed.

Both passive five-second UART windows pass the previous idle flood criterion:
85.29-86.30/s before, 85.39-86.32/s after, no runtime UART patch module/endpoint.
This is IRQ evidence only, not charging or performance acceptance.

## Battery regression remains unresolved

User reports that after extended plugged-in time, unplugging immediately gives a
low-power warning, unlike before our flash. Treat this as an unresolved reported
regression. The earlier successful powered boot and exact image readback did not
qualify charging or battery reporting. No retained voltage, charge-current,
charge-state or shutdown telemetry establishes the cause. The plugged-in game
return likewise cannot establish battery health or charge behavior.

Offline inspection of the exact captured rootfs locates stock vrtemu ADC/display
code and `/dev/adc`; the same image contains gp_adc_module and adcset.ini thresholds
315,310,290,285,280. The entire rootfs matches pre-kernel-patch Wings2, so these
bytes are unchanged. These are raw vendor thresholds, not calibrated voltages or
proof of a charging control path. Unchanged power-related code does not exclude
indirect kernel/UART effects or hardware/charger causes. Do not blame low battery
or clear our change without a controlled power observation.

Next priorities: diagnose the battery warning; add visible cold-replay progress,
durable call count/abort source and bounded progress evidence before another suite.
The previous repeat left the silent replay unchanged and did not resolve its
observability failure. No more unchanged rearm. Keep firmware acceptance scoped
to exact image installation, boot screens and bounded IRQ behavior.

[Return receipt](../evidence/2026-10-16/fivegame-kernel/return.json).
Reproduce from the immutable sparse archive with `build/report-fivegame-kernel.py`
(once; output refusal protects existing analysis), then
`build/evaluate-fivegame-kernel-return.py`. Raw ROMs/states/captures stay private.
