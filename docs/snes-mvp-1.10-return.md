# MVP1.10 return: driver failure mislabelled as queue overflow

The user reports a failed first launch, a working retry, then a failure around
snapshot load and fallback to stock. Read-only collection archives 43 MVP and
49 lab files. All payload hashes match 1.10; the game one-shot is consumed.
Nineteen previously protected game-progress files, including every snapshot,
are unchanged. FF6 SRAM changed during play and is archived before updates.

Both final reports survive. The first has 72 core calls, no pauses, one WRITEI
failure and 2,823 priming frames. The second has 605 calls, one pause and 5,646
priming frames, proving startup and a re-primed resume. Both report EBADFD (77)
from WRITEI, a software high of 2,823/8,192 frames and 705 unaccepted frames
remaining. Their software accounting balances. The queue was not full: the
runner incorrectly labels every publication failure as overflow, including a
prior worker error. No snapshot load-success counter existed in 1.10.

First active-loop throughput is about 56.98 calls/sec; second is about 59.70.
Second mean core wall is 10.61ms and main-thread CPU is 9.93ms. These are short,
fatal sessions, not sustained full-speed acceptance. Zero intentional holds
remain; one final drawing per attempt is omitted after the audio error becomes
fatal. The second sampled playable minimum is 134 frames (about 3.04ms).
Its 64ms initial reserve is not a guaranteed later minimum.

Error details identify WRITEI exactly, but retain the preceding observation:
SETUP in the first attempt and RUNNING/229 frames in the second. They do not
capture the actual post-fault state. The kernel capture now proves `dmesg` is
absent. No kernel-ring or driver implementation evidence follows. Wrapper
status 255 follows a recorded library B exit and completed display join/cleanup;
this return supplies no new whole-device poweroff or process-signal evidence.

The owner requests refresh before admission but does not wait for it. A
counterexample with a cached 32-frame lead and actual 128-frame lead rejects the
exact shipped owner and passes the repair. This establishes a source defect,
not sole causation of the vendor error. Linux 4.19
[STATUS](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/pcm_native.c)
also copies state before updating the hardware pointer; SYNC_PTR with HWSYNC
and both GET flags returns post-update state/control without changing them.
The repaired client uses that interface and negotiated-boundary arithmetic,
captures post-WRITEI-error state, and restores period readiness after DRAIN.

[1.11](snes-mvp-1.11.md) keeps the same core, parameters and full drawing. A new
real-core test runs the actual native client/owner through an injected WRITEI
failure, clean retry, two snapshot loads/resumes, consuming PCM and 25ms stalls.
All 120 successful drawings and PCM accounting are retained. This is stronger
lifecycle evidence than the earlier nonconsuming mock; it cannot qualify the
vendor driver or explain every audible/device failure.
