# MVP1.19 return: Bio Blast still exhausts audio production

Ben reports that Bio Blast still crashed the game, then he exited the menu
with B. The current native reports confirm an audio failure and return to our
library. B subsequently left that library. Startup records display-worker join,
FreeVFB completion and board close; the wrapper records normal process exit255
and completes its final diagnostic copies. The process returned rc=-1 from the
failed game. This is not a recorded signal crash or whole-device power-off.

The one recorded game launch ran 1,713 core calls in 28.62062 seconds of active
time, about 59.852 calls/sec. A snapshot load succeeded. No drawings were held
and no duplicate video callbacks occurred. The final failed audio callback
prevented one last drawing, leaving 1,712 submissions. First-attempt startup
reliability and complete effect fidelity are not independently established by
this short failure run.

The last 23 ordinary calls average **18.287 ms wall / 16.935 ms main-thread
CPU**, against a 16.688 ms native frame budget. In the retained 227.816 ms PCM
interval, 13 matched large-batch anchors account for 8,831 accepted frames:
**38,763.739 frames/sec versus the negotiated 44,100 Hz sink**, a 12.10% deficit.
Accepted sound trails reported hardware advance by another 1,153 frames over
that interval. Reserve erosion precedes an unexplained application-pointer
difference of384 frames: observations first see+128, then another+256. The
stream subsequently reports SETUP and SYNC_OBSERVE errno77/EBADFD; no XRUN state
was recorded. This remains a transient underproduction lead, not identification
of who changes the pointer or the vendor's exact stop mechanism.

The recovered1.18 ordinary-call costs were18.328 ms wall /17.001 ms CPU, and its
matched accepted rate was38,512 frames/sec. These are different runs, encounter
timings and call histories. They are context, not a controlled cache-speed
comparison.1.19's33.56% reduction in offline palette lookup rows has **not fixed
physical audio continuity**, and cannot be presented as a measured A7 speedup.

No phase sample falls inside the final24-call window. The last earlier sample
is call1668; the failure is call1713. Earlier inclusive PPU/APU timings therefore
cannot reliably assign this final deficit. Before another optimization, the
next engineering step is bounded RAM-only phase attribution during the actual
expensive interval, with instrumentation cost and any induced slowdown reported
separately. Do not silently restart PCM, omit emulated frames or re-arm unchanged
1.19 as if another run tests a new fix.

Return archive `device-evidence/snes-mvp-return-20261010T071438Z` preserves58
MVP/progress files and49 lab files with source/copy/source hash verification.
All prior files remain present; nine private snapshots retain hashes and valid
payload CRCs. All three SRAM generations are8,192 bytes and unchanged from the
pre-rearm archive. This establishes byte preservation, not an in-game semantic
save test. Exact1.19 runner/core/wrapper, stock hashes and normal init verify.
Fresh read-only CHKDSK reports the known FAT card clean; no repair is needed.

Independent live rereads verify all58 archived MVP/progress files, current
stock/Vesper SD artwork and normal init. All armed markers and Code.bkp are
absent. No card write, repair, save restoration, payload change or firmware
operation occurred. Both accepted Vesper firmware screens remain outside this
SNES change. Completed wrapper copies and clean FAT qualify this returned
shutdown sequence; they do not establish universal hard-power-off safety.

The native final session, unique failure session and copied RAM checkpoint
agree on gameplay/failure fields. Only checkpoint/elapsed times and the final
RAM-write accounting differ. Unlike previous returns, last-run.log is fresh:
its error detail matches this session. A guarded publisher verifies the raw
archive, release, progress, PCM and exit identities, and publishes only text
diagnostics and derived metadata. Games, snapshots, SRAM and vendor binaries
remain private.

[Verified analysis](../evidence/2026-10-10/snes-mvp-1.19-return/analysis.json),
[PCM history](../evidence/2026-10-10/snes-mvp-1.19-return/pcm-failure.txt),
[clean FAT](../evidence/2026-10-10/snes-mvp-1.19-return/chkdsk.txt),
[independent readback](../evidence/2026-10-10/snes-mvp-1.19-return/independent-readback.json).
