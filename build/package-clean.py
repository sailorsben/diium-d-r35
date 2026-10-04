from pathlib import Path
from hashlib import sha256
import json
import zipfile
root=Path(__file__).resolve().parent.parent
build=root/'build/clean'
out=root/'SNES-Plus-clean'
out.mkdir(exist_ok=True)
def digest(p): return sha256(p.read_bytes()).hexdigest()
assert (build/'verification/audio.s16le').read_bytes()==(root/'build/v2/verification/audio.s16le').read_bytes()
assert not (build/'verification/adapter.log').exists()
checks=(build/'checks.log').read_text()
for phrase in ['PASS recovered chunk ioctl ABI','PASS resampler:','PASS frames=1800']:
    assert phrase in checks
core=build/'emu_sfc_plus.so'
assert digest(core)=='1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
(out/'README.txt').write_text('''DIIUM D-R35 -- clean stable SNES Plus adapter

Playback is based on the proven v2 adapter: two alternating chunk-memory video
buffers, packed RGB565 rows, safe geometry handling, continuous 32040-to-44100
sample conversion, ZIP loading and tagged Plus states. The upstream Plus core
is unchanged. The only change to v2 is that D35_PLUS_LOG must be explicitly set
to enable a log; ordinary device launches create no automatic diagnostic logs.

There is no PCM capture ring, diagnostic worker, timing/queue polling, write
audit or frozen/black display experiment in this adapter. The original frontend
audio callback is restored. Only retro/libs/emu_sfc.so is updated. Retain
emu_sfc_plus.so alongside it. Original emulator and game/save files are retained.

Clicking remains unresolved. Evidence as of this cleanup:
- Graphics and music warbling were fixed with the Plus core/chunk-buffer adapter.
- The handheld v6 PCM recording sounded clean to the user when played on PC.
- V7 accepted all 2,975,744 submitted bytes, with no partial/failed writes.
- V8 accepted all 6,982,240 submitted bytes, with no partial/failed writes.
- One full frozen-picture and black-picture interval ran; neither audibly
  changed the clicking. V8's returned WAV and timing report were empty, so they
  cannot be used as further audio/timing evidence.
- User reports Ninja Gaiden NES sounded clean; outdoors in FFVI still clicks,
  while houses, combat and victory music were reported clean.
These observations do not distinguish kernel playback/DMA faults from an audio
output issue that depends on signal content. A second SNES game is a useful
comparison before changing playback again. No clicking fix is claimed.

Cleanup: twenty old emulator diagnostic files were archived and removed from
D:, followed by the six v8 diagnostic outputs. Evidence remains on the PC.
The screen-size flash test remains removed from init. No further experimental
build was installed during this cleanup. This clean adapter replaces v2 only
to disable its automatic logging. Games, saves, core and other retro files were
verified unchanged during restoration and installation.

Verification: ARM/QEMU using device glibc 2.30; FF3 output is byte-for-byte
identical to v2. Chunk-buffer layout/lifetime, resampling, safe geometry and
tagged state save/load checks pass; default run produces no adapter log.
The underlying v2 playback was tested on the handheld. The logging-only change
has not had a further handheld run.
''')
with zipfile.ZipFile(out/'SNES-Plus-clean-update.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(build/'emu_sfc.so','retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-clean-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(root/'SNES-Plus-v2/SNES-Plus-v2-source.zip','v2-full-source.zip')
    for name in ['emu_sfc_plus_clean.c','adapter-check-clean.c','video-contract-check-clean.c',
                 'build-clean.sh','run-clean-checks.sh','prepare-clean.py','harness.c',
                 'package-clean.py','install-clean.py']:
        z.write(root/'build'/name,'build/'+name)
manifest={'build':'clean stable v2 playback; no automatic log',
          'adapter_sha256':digest(build/'emu_sfc.so'),'core_sha256':digest(core),
          'expected_before_sha256':'4a805d19446fad487cf3c43a6b74bbed7027d6af037df1c9f393426a403cabb5',
          'audio_matches_v2':True,'no_automatic_log_in_harness':True,'clicking':'unresolved',
          'packages':{p.name:digest(p) for p in out.glob('*.zip')}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
