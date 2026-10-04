from pathlib import Path
from hashlib import sha256
import json
import zipfile

root=Path(__file__).resolve().parent.parent
out=root/'SNES-Plus-v4-diagnostic'
out.mkdir(exist_ok=True)
def digest(p): return sha256(p.read_bytes()).hexdigest()
shim=root/'build/v4-diagnostic/emu_sfc.so'
core=root/'build/v4-diagnostic/emu_sfc_plus.so'
rollback=root/'device-evidence/card-D-v2-return/emu_sfc.so'
prior=root/'device-evidence/card-D-v3-return/emu_sfc.so'
assert digest(prior)=='2f427f7b758839feccc314ad3799e8676ec5e1ff26a468ed447fd892ff756033'
assert digest(rollback)=='4a805d19446fad487cf3c43a6b74bbed7027d6af037df1c9f393426a403cabb5'
assert digest(core)=='1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
assert digest(root/'build/v4-diagnostic/verification/audio.s16le')==digest(root/'build/v2/verification/audio.s16le')
checks=(root/'build/v4-diagnostic/checks.log').read_text()
for required in ['PASS periodic FF3 timing log exists at frame 900, before serialization/unload',
                 'PASS periodic report before exit/save; no gameplay wait; worker joins promptly',
                 'PASS frames=1800', 'PASS diagnostic:', 'PASS resampler:',
                 'PASS recovered chunk ioctl ABI']:
    assert required in checks,required
readme='''DIIUM D-R35 -- SNES Plus v4 DIAGNOSTIC

This corrects a v3 diagnostic gap: the tested handheld run returned only the
startup log, with no timing report. Exit/unload/serialization cannot be relied
upon to flush RAM measurements for this frontend/session.

V4 saves a snapshot every ten seconds using a background thread with a lower
CPU scheduling priority. Gameplay callbacks use try-locks; they never wait for
the reporting thread. Snapshot copying occurs under a short measurement lock;
all disk I/O occurs after that lock is released. Skipped measurements are counted.
Reports are written to a temporary file, flushed, and renamed over the previous
complete report. Directory flush is attempted when supported. Exit/save-state
flushing remains available; a library-unload destructor joins the worker too.

The emulator core, v2 chunk-backed alternating video buffers, continuous sample
conversion, controls, ROM handling and save-state format remain unchanged.
Diagnostic storage: 172088 bytes; worker stack allocation: 128 KiB, plus pthread
and stdio runtime overhead. Queries of the existing driver's DSP descriptor are
read-only. There is no change to audio writes, sample rate, device format, device
buffer configuration or frame pacing. This is not a claimed clicking fix.

Test the wind scene, combat entry and victory music. Note approximately when
clicking occurs. Use ESC -> Exit when finished; reconnect as D:.
Normal snapshots no longer require saving a state or a successful core exit.
The report can lag the latest gameplay by roughly ten seconds.

Logs under retro:
  emu_sfc_plus_v4.log          Startup and reporting-worker status.
  emu_sfc_plus_v4_timing.log   Latest complete timing and queue measurements.
  emu_sfc_plus_v4_timing.log.tmp may exist if writing was interrupted.

Installation replaces only retro/libs/emu_sfc.so. Leave emu_sfc_plus.so alongside
it under its existing name. Rollback restores the proven working v2 adapter.

Verification: ARM/QEMU with copied device glibc 2.30, including its pthread and
loader libraries. Captured FF3 audio is byte-for-byte identical to v2. Video
buffer contracts, resampling, tagged states, unsupported OSS queries and bounded
event retention pass. The periodic file was observed at frame 900, before any
serialization or unload. A busy measurement lock did not block the caller; the
reporting worker joined promptly. Physical playback timing remains untested.
'''
(out/'README.txt').write_text(readme)
with zipfile.ZipFile(out/'SNES-Plus-v4-diagnostic-update.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(shim,'retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v4-diagnostic-rollback-to-v2.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(rollback,'retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v4-diagnostic-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(root/'SNES-Plus-v3-diagnostic/SNES-Plus-v3-diagnostic-source.zip','v3-full-source.zip')
    for name in ['emu_sfc_plus_v4_diag.c','audio_diagnostics_v4.h',
                 'audio-diagnostics-check-v4.c','adapter-check-v4-diag.c',
                 'video-contract-check-v4-diag.c','harness-v4-diag.c',
                 'build-v4-diag.sh','run-v4-diag-checks.sh','prepare-v4-diag.py',
                 'package-v4-diag.py','install-v4-diag.py']:
        z.write(root/'build'/name,'build/'+name)
manifest={'build':'v4 diagnostic','adapter_sha256':digest(shim),
          'core_sha256':digest(core),'rollback_v2_sha256':digest(rollback),
          'expected_before_sha256':digest(prior),
          'diagnostic_storage_bytes':172088,'worker_stack_bytes':131072,
          'report_interval_seconds':10,'periodic_report_before_exit_verified':True,
          'test_pcm_sha256':digest(root/'build/v4-diagnostic/verification/audio.s16le'),
          'hardware_test':'pending','packages':{p.name:digest(p) for p in out.glob('*.zip')}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
