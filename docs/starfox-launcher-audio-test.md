# Interactive Star Fox native audio test

I: is armed for one boot from `019704d`. The full readback checked 2,197
files, both markers and clean FAT32. All 2,193 protected prior files
match their baseline hashes.
[Arming receipt](../evidence/2026-11-12/starfox-launcher-audio-arming.json).

The one-boot launcher runs the same Star Fox cartridge and optimized core
(`70d8851`) as the previous interactive test. Only the matched Star Fox
cartridge activates native PCM and display backpressure handling. New and
Classic artwork, menu audio, controls, private state paths and other games
retain their existing routes.

## Handheld procedure

Safely eject I:, then cold boot the handheld. Launch **Star Fox** and play
through the title screen and at least two minutes of Corneria. Note whether
you hear clicks and roughly where they happen. Open the pause menu once,
resume, and keep playing briefly. Use **Menu → Exit** to finish writing the
audio log before shutting down and reconnecting the card. The next boot
returns to stock.

## Audio and display ownership

The stock menu waits for its audio producer to exit before entering the
game. The launcher closes the pinned driver's OSS descriptor, then the
native worker opens `/dev/snd/pcmC0D0p` at 44,100 Hz with a 128-frame
period and a 7,552-frame buffer. PREPARE precedes the final software
parameters because the vendor driver rewrites them. Playback starts
explicitly after accepting 6,615 frames of priming silence. Audio reserve
gates gameplay production in place of the stock sleep. Core PCM still
uses the existing continuous interpolation. Pause drains and closes the
native device, and Resume opens a fresh stream. The menu writer is reopened
after game cleanup. A native error follows the stock exit path so a fallback
cannot masquerade as a successful test.

The pinned display driver exposes one source credit in
`DisplayThreadflag`. The gameplay producer can submit only when the scaler
is running and has released the previous source. The scaler clears that bit
after reading the source. The gameplay thread owns submission during the
game. A busy credit skips only presentation. Core ticks, input, rendering
and audio generation continue, with emulation frame skip off. The normal
256×224 scaler input and border handling remain in use. Pause and exit still
fence display ownership before the UI or the cleanup reuses its buffers.

## Physical acceptance

The [FFVI burst test](presentation-ffvi-return.md) showed a recovery gain.
Both nonblocking 48 ms candidates completed, with both blocking controls
failing. The [Corneria replay](starfox-fullscreen.md#corrected-handheld-return)
ran 1,200 ticks in 19.975 seconds, used 16.042 s core thread CPU and 0.309 s
display worker CPU, and retained at least 5,042 playable frames with zero
underruns. These are handheld measurements from standalone runners. The
interactive patch has no measured A7 CPU saving or device-side logging cost.

For a matched interactive trace, CPU breaks even when avoided stock writer
and avoided display-job CPU exceed native writer, wake/admission and trace
CPU. Avoided blocking wall time belongs in the deadline calculation, not
the CPU saving. At 59.922743 ticks/s the per-tick budget is 16.688 ms and
the 44.1 kHz sink consumes about 736 stereo frames per tick. With 6,615
primed frames and a 256-frame margin, cumulative drawdown must stay below
6,359 frames. The standalone replay's observed low point leaves 4,786
frames above that margin. An equivalent interactive window can absorb that
much additional drawdown. The absolute live deficit is unknown until
measured because actual inputs and the stock display path can change the
production curve. This one-boot run measures the audio repair, not an
interactive performance promotion.

Each gameplay segment writes its own `retro/d35-launcher1/starfox-audio-*.log`.
The log records admissions, tick and presentation durations, generated and
accepted frames, hardware/application pointers, playable reserve, PCM
state, minimum reserve, maximum write gap, underruns and pointer drift.
The trace stays in RAM during gameplay and flushes at pause, normal exit,
or a handled fault. It retains the latest 16,384 ticks (about 4½ minutes)
per segment and reports the retained start index. A sudden shutdown can
leave a start-only log. Handoff failures before PCM opens have a separate
`starfox-audio-handoff.log`.

Check that each segment has a complete report, 6,615 accepted prime frames,
one START, zero XRUNs and pointer mismatches, and
`accepted == generated + prime` on drain. Look for queue drawdown and later
recovery across the audible interval. The hardware counters establish sample
delivery. The listener's report establishes whether clicking is gone.
