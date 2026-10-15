# Unchanged-core PC diagnostic armed on I:

Historical installation record. The diagnostic has now returned; I: is unarmed.
See [results and current evidence boundaries](snes-pc-profile-return.md).

Ben explicitly requested "Arm I" after the deeper efficiency research.
Installed `1.19-pc-profile1` from clean, pushed commit
`6123047df25cc6f3cb3a8b21d84532f68041af9a` on 2026-10-14 America/Chicago.
Physical attribution and sampling quality remain **PENDING**.

Fresh private archive `device-evidence/a7-pair-before-20261015T001121Z`
preserves all 7,226 retro files / 1,827,485,639 bytes. Every file matches the
previous evaluated return; none was added, removed or changed. FAT was clean.
The guarded installer verifies the pinned qualification, sources, payloads,
boot/adapter/production core and ROM before installation. All 88 separately
owned payloads at `I:/retro/snes-pc-profile1` read back exactly. The 7,225 prior
files other than the authorized dispatcher remain exact, including original
progress and prior tests. ROM remains exact. FAT is clean before installation,
after payload staging and after arming. Only the existing MVP dispatcher and
one-shot marker select this test. The publication check preserves every prior
published hash and frozen preparation artifact.

Both `cores/reference.so` and `cores/demand.so` contain the same ordinary
demand-v3 ELF, SHA256
`1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8`.
The controller runs four epochs, up to 1,200 calls each:

| Order | Effect | Main-thread PC sampling |
| --- | --- | --- |
| 1 | Meteor | Off |
| 2 | Meteor | On |
| 3 | Quasar | On |
| 4 | Quasar | Off |

The sampler records frame and ELF-relative PC in RAM during `retro_run`, then
flushes after workers join. It retains delivered counts, overruns, dropped
counts, full frame/PCM histories and native pointer telemetry. Timer support,
actual resolution, usable owner distribution and sampling disturbance must be
evaluated on return. Requested 1ms is not guaranteed delivery resolution. The
priority prototype and compiler-control cores remain local research artifacts;
no optimization or production acceptance is established by this diagnostic.

Safely eject I:, cold-boot with the handheld initially off, allow **3–5 minutes**
for the four epochs and flushing, wait for the stock launcher, then power down
and return I:. Select+Start aborts. The wrapper consumes the marker before
hardware startup; the following reboot is stock. Archive on return before
updating or rearming. Analyze the exact installed ELF with `build/analyze-main-pc.py`,
retain control/sample disturbance, and reject mock or invalid-pointer evidence.
Sparse samples must not be converted into invented time or unit-cost claims.

The prepared `ready.json`, plan and pinned test instructions remain historical
preparation receipts. This installation is recorded separately in the
[verified installation receipt](../evidence/2026-10-14/pc-profile/installation.json).
See the [research and measurement limits](snes-deep-efficiency-research.md).
