# D-R35 project continuity

Read README.md, docs/boot-and-hardware-contracts.md, docs/investigation-history.md and the latest CHANGELOG.md entry before resuming device work. Use docs/device-findings.md for the current evidence boundaries. Older reference reviews may contain superseded hypotheses.

- GPIO200/201/202/203 are Up/Down/Left/Right. Native masks 10/40/80/20 hex must be interpreted through the stock libretro table, not assumed bit conventions.
- Signal /tmp/vrtemu.log and wait for active showlogo processes to exit before InitVFB. Its final cleanup can otherwise overwrite or destroy a live display.
- Read scheduling time through the kernel syscall and use relative remaining-duration waits. Libc CLOCK_MONOTONIC was directly observed disagreeing severely with the kernel clock.
- Own chunk-backed RGB565 buffers and retain them until the display worker has finished. Join before freeing buffers or the display.
- On card return, archive logs and all private progress before updating or re-arming. Preserve stock binaries and saves by hashes. A consumed one-shot marker makes the next reboot stock.
- Test the actual seam that failed. Independent stock-derived fixtures outrank tests that repeat our own assumptions. QEMU checks are not physical input/audio/display or performance evidence.
- Keep discoveries, corrections, negative results, verification and next physical test in documentation and Git history with source changes. Push authorized work to the configured remote.
- Do not add ROMs, private states/SRAM, full card backups, vendor binary dependencies, credentials or local attachment/account material to publication commits.
- Source installers under build/ include historical, path-specific experiments. Read their guards before using them; do not treat every script as a current install instruction.
