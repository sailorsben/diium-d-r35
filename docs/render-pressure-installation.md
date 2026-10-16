# ROM-free pressure test armed on I: — 2026-10-15

Installed and armed `render-pressure1` from pushed source
`26e9d3d7744c5185885beb069be9673894f282b1`. The 70-phase workload and offline
qualification are described in [the lab design](render-pressure-lab.md).
Physical acceptance and performance results remain **PENDING**.

Fresh strict archive: `device-evidence/a7-pair-before-20261016T032746Z`.
All 8,274 protected prior retro files are preserved exactly; the authorized SNES
test dispatcher is the sole changed prior file.
The versioned `retro/render-pressure1` package contains the executable, wrapper
and frozen qualification. Both owned one-shot markers are armed. The permanent
UART correction, emulator/core, ROM, saves and previous logs remain preserved;
there is no firmware update payload. FAT checks pass before staging, after
payload verification and after arming. Independent readback checks the prior
files, installed payloads, exact marker bytes, dispatcher, ROM and UART state.

[Installation receipt](../evidence/2026-10-15/render-pressure1/installation.json)
and [independent verification](../evidence/2026-10-15/render-pressure1/live-verification.json)
bind the hashes and protected-file count. Preparation/qualification receipts
remain the original offline records; installation is separate evidence.

Safely eject I:, cold boot the handheld and allow about 5–6 minutes. The test
shows generated patterns and plays quiet test audio. Some cells intentionally
apply excessive CPU load; their failures are useful measurements. Select+Start
aborts. On normal completion it returns to the stock launcher. If it remains in
the test or has not returned after about six minutes, power it off and return
the card for collection. Forced/uncertain child termination deliberately holds
stock until reboot. Both markers are consumed before hardware startup, so the
following boot is stock with the permanent UART correction still enabled.

Logs land in `retro/render-pressure1/results/run-<boot_id>-<pid>`. Archive them
and all private progress before any rearm or update. Do not infer device speed
or a hardware ceiling from the offline mock or successful installation.
