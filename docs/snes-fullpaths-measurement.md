# Five-core A7 crossover measurement — 2026-10-13

Ben explicitly authorizes staging an automated measurement on I: for the three
full-fidelity paths separately and combined. This is measurement-only authority;
the production installation gate remains false until the returned device proves
the actual saving, costs and complete effect/recovery behavior. Every frame and
sample remains required. No nominal-MHz or QEMU-duration performance prediction
is substituted for the missing A7 measurement.

## Matched schedule and identity

The five variants are the qualified ability2 baseline, fixed-row private-v3,
true-subscreen private-v1, DSP dead-work private-v1, and their new combination.
The first four binaries are reused byte-for-byte with their frozen hashes and
offline proof. The combination is derived from fixed rows and applies each of
the other two source patches once; it receives new output qualification.

Ten contexts span the distinct exposure populations: Holy, Meteor, Meltdown,
Siren, Bahamut, Carbunkl, Quasar, Lullaby Rage, Bio Blast and Confuser. Each variant
gets the same input trace, target, logical state and 1,200-call bound. Only each
snapshot's 40-byte identity header changes to the exact core CRC/size; logical
state payloads and input/expected-property files stay unchanged. No ROM patch.
The runner's separate identity header encodes the exact 100-run schedule; begin,
result, session, plan and installation records identify every variant/fixture.

Round one uses ascending cases and baseline/fixed/subscreen/DSP/combined. Round
two reverses both orders. These repetitions expose order/warm-up variability;
two repeats do not establish a confidence interval or thermal worst-case proof.
Total nominal gameplay is 33.376 minutes plus loading and flushes. Native errors
retain the failed run and continue with independently reset audio/core state;
no hidden recovery, reprime or error suppression is added. MENU aborts the suite.

## Clocks, logging and headroom

The same owned runner observes every variant with kernel thread-CPU and scheduling
clock syscalls. Nested core phase clocks stay disabled. It records call CPU/wall,
total step, observer time, main-step CPU, audio/display worker CPU, native quota,
PCM pointers/reserve, submitted/flipped frames and frequency before/after calls.
Existing sysfs inspection/pinning/restoration remains: raise min to the existing
max only if exposed on the single CPU, record readback, restore the original min.
Unexposed frequency stays explicit; never assume sustained 666 MHz.

All per-frame rows remain in RAM. Identity observation, clocks, frequency reads
and record copies stay included. The observer's own measured duration is logged
separately, never subtracted as calibration. Normal wrapper discovery, file writes
and global sync occur outside live measured gameplay; per-run flush happens only
after audio joins and the display becomes idle. The native fault path remains a
bounded terminal diagnostic, not a normal performance sample.

Audio admission has three possible waiting reasons: fresh device observation,
software queue capacity, or deliberate pacing because lead exceeds the prime
target. Only a wait with fresh observation already complete, sufficient capacity
and excess lead is tagged as pure intentional pacing. All other admission cost
remains work. The tag adds included clock calls and does not change the wait,
stream, buffer or thread scheduling decisions.

The service proxy is `step - verified pure pacing wait + all audio/display
worker CPU deltas`. Some worker CPU is already in the remaining wall interval;
adding it again deliberately makes this proxy conservative. It is not an exact
non-overlapping partition. Pointer divergence, malformed clock/delta accounting,
an incomplete run or a missing drawing prevents a positive headroom flag.
Compare the proxy with the cycle-derived 16.6881545 ms deadline and the proposed
13.3505236 ms target (20% capacity margin). Do not treat paced wall duration as
absence of spare capacity.

`headroom.txt` records mean/median/p95/p99/max, overruns, frame completion,
included observers and accounting validity. Its warm distribution excludes the
first 120 calls; raw rows retain those calls. `MET_IN_THIS_WARM_SAMPLE` requires
every warm sampled frame below the target, all 1,200 drawings complete, no native
error and valid accounting. It is explicitly a sampled result, never universal
effect/production acceptance. Full-effect/recovery and cumulative reserve require
the returned trace, including earlier cold frames and peripheral work after the
last main call. No standalone unit prices are manufactured from whole-call time.

## Offline qualification and physical prediction

New combination qualification compares pixels/geometry/native PCM each call and
normalized state every 30 calls against original 1.19 across 18 contexts. Hashes
reuse existing standalone exactness rather than repeating unchanged core tests.
The actual new controller exercises all 100 runs under the null backend, checks
core/state identities, expected properties, 1,200 submissions per run, exact PCM
accounting and rejects mock timings as physical headroom. The consuming native
fixture checks EBADFD preservation, clean retry, sustained deficit and teardown;
the exact wrapper fixture checks absent head/sed and splash/one-shot ownership.

Nine independent accounting fixtures reject mock timing, pointer drift, missing
drawings, malformed waits, regressing worker clocks, a tail overrun, a fatal run
and a short run. Synthetic return-model fixtures also check the direction of a
known matched saving, a negative combination interaction, missing flips and
incomplete heavy-frame overlap. Those fabricated inputs test the parser and
arithmetic only; they are never A7 evidence.

The falsifiable prediction is comparative, with unknown A7 prices: fixed-row
savings should be concentrated in Siren/Carbunkl/Lullaby; full-add composition in
Holy/Meltdown/Quasar/Bahamut; DSP savings should track silent-voice exposure after
its new branch cost. Meteor has few new full-add rows and modest setup removal.
The combined result may differ from the sum; never assume additive savings.
The existing aligned targets range up to 5.354 ms net saving for the proposed
margin. Failure to reach it is a measured candidate failure, not proof of an
unavoidable hardware limit.

The return analyzer uses exactly matched frame indices, retains missing/partial
overlap and reports each path's CPU/wall/service differences and the combination's
extra gain versus the sum. Fresh baseline failure positions and wider recovery
must also be inspected; the previous 16-frame heavy interval is a fixed comparison
anchor, not a replacement for the complete trace. Frequencies/pinning, every-frame
completion, quota and pointer/reserve validity accompany any physical verdict.

## Archive, installation and construction corrections

Archive every retro file with source/copy/source SHA before card writes; require
fresh clean FAT serial 11EB-1465 and no armed marker or firmware update trigger.
Preserve every old file except the known one-shot dispatch wrapper. Install only
the owned `retro/snes-fullpaths1` folder, verify all payloads and protected files,
then consume the marker on boot. Production `emu_sfc.so`, cores, init, ROMs and
original progress stay unchanged. The next reboot returns to stock.

The first source generator expected the older optional-profile guard, but the
ability2 runner already explicitly disabled those clocks. Its assertion stopped
before building or touching the card; that partial tree is retained privately.
The corrected generator asserts the existing disabled state. The new main also
avoids host `strtoul`'s C23 ABI, absent from device glibc 2.30, using a bounded
decimal parser instead. These are build corrections, not A7 performance results.

[Physical instructions](snes-fullpaths-test.txt), [mechanisms and targets](snes-full-fidelity-paths.md).
