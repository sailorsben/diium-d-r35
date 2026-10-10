# SNES focus1: installed diagnostics, physical result pending

The installed1.19 core remains byte-identical. Runner1.19-focus1 adds bounded
phase/callback CPU capture around expensive calls. This is a diagnostic run,
not an audio fix. See [test instructions](snes-focus-1-test.txt) and the
[ROM-derived investigation](ff6-bio-blast-cause-map.md).

Baseline1.19 fails Bio Blast with audio underproduction, but its final24 calls
have no PPU/APU phase sample. Focus1 keeps64 recent frames and samples one in
eight during a96-call burst after an ordinary call reaches16ms wall or15ms CPU;
the normal cadence remains one in64. Sampled calls cannot extend the burst.
Sampling uses kernel thread CPU clocks and measures real callbacks. Timer
overhead remains included, callback CPU can overlap inclusive APU time, and
residual work includes SPC execution through ports. Never add overlapping
regions or subtract a calibration number as exact overhead compensation.

The actual ARM runner passes180 rendered core frames and exact PCM accounting,
independent resampling, all64 cadence offsets over the returned failing costs,
feedback exclusion,64-record reporting and the consuming native PCM seam:
fault/retry, two snapshot loads, drain and sustained production deficit.
The analyzer accepts the actual report and rejects duplicate fields, wrong core
identity and callback/run mismatch. These are offline contracts, not physical
timing or successful sound.

`device-evidence/snes-mvp-return-20261010T144407Z` archives58 MVP/progress and49
lab files before writes. Clean known FAT, current boot baseline and138 protected
file hashes verify, including27 SPI-reader files. The installer replaces only
the owned diagnostic runner and instructions, then arms the SNES one-shot.
Independent readback preserves all archived bytes, exact core/wrapper and clean
FAT; lab and firmware triggers remain absent. A read-only payload/marker check
at15:42UTC still finds the expected focus1 test armed. No later candidate was
installed.

| Payload | SHA256 |
|---|---|
| Runner,110,412 bytes |`7100b40f608f48ac141c1293e452c0467837ea33f87816623182b81df2c57999` |
| Unchanged1.19 core,789,764 bytes, CRC32 `3d35ed49` |`80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8` |
| Unchanged wrapper |`35b1c32fa5924e33a0f1da47833b6710e53dadc5ebd832a6b998a86236e2cc13` |

The owned runner release is `releases/snes-focus-1`; core/runtime dependencies
and private progress are not published. Curated
[qualification](../evidence/verification/snes-focus-1/verification.json),
[installation](../evidence/verification/snes-focus-1/focus-installation.json) and
[independent readback](../evidence/verification/snes-focus-1/independent-focus-readback.json)
retain evidence boundaries. The publisher preserves all645 prior evidence hashes.
Three existing UI sources retain their qualified trailing CRLF through explicit
Git attributes; their code is unchanged. This preserves the source hash inputs
of the captured runner rather than silently normalizing its publication proof.

On return, strictly archive first and obtain fresh FAT health. Verify the
runner/core identities and consumed marker, then run `build/analyze-snes-focus.py`
against the actual session. Separate ordinary and instrumented calls. No live SD
polling, intentional frame suppression or altered PCM admission was added.
Select+Start -> Exit game while running; B leaves our library. Wait for the
stock launcher before the physical power button.
