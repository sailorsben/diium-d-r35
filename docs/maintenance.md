# Maintaining evidence and continuity

The guides are current interpretation; `evidence/manifest.json` identifies published artifacts and original provenance. Dated reference reviews retain historical assumptions. Correct a conclusion in the current guide and explain why; do not rewrite a raw device return to make it fit.

## Each device iteration

1. State the concrete failure and what observation would distinguish causes.
2. Collect/archive the returned run and all private progress before mutation.
3. Compare actual binaries/boot hook/markers with the expected version.
4. Fix the owning seam. Test actual entry/input/timing/transport paths, with independent references where available.
5. Preserve original/private saves and stock binaries; verify writes and guards.
6. Record installed binary/wrapper hashes, local checks, physical results and the next pending test.
7. Update guide/changelog/source/evidence together, commit explicit paths and push authorized work. Verify the remote commit rather than claiming publication from a local commit alone.

## Publication boundaries

Version authored source and portable instructions, selected logs/ABI measurements and owned executables. Do not publish ROMs, personal SRAM/snapshots, full SD/firmware exports, device libraries or credentials. Public evidence is selected and path-normalized; its manifest distinguishes original hashes from published hashes. Full local archives remain available for device-specific recovery.

Root source contains historical guarded installers. Stable guides identify the current workflow and avoid presenting stale paths/hash checks as generic commands. A fresh checkout needs separately supplied dependencies; documentation must say that clearly.

## Before re-investigating

Check the hardware contracts for splash cleanup, GPIO→native→callback translation, libc/kernel clock disagreement, chunk/DMA ownership, void audio return ABI, geometry callback corruption and supervisor/watchdog distinctions. Check history for the UART-redirection negative result, map/menu workload control, render-disabled experiment and corrected timestamp parser.

Maintain confidence boundaries: observed on-device, exact binary analysis, local fixture/QEMU, supported inference, and unknown are different. The latest observation does not erase a working baseline; a successful build does not finish a physical test.
