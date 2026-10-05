"""Publish a selected, path-normalized evidence set; never copy ROMs or saves."""
from pathlib import Path
from hashlib import sha256
import json
import shutil

ROOT=Path(__file__).resolve().parent.parent
# This exporter preserves the historical1.5 build. Refuse before writing any
# outputs if the live build has advanced; publish1.6 through its own exporter.
assert json.loads((ROOT/'build/snes-mvp/out/verification.json').read_text()).get('version','1.5')=='1.5', 'Historical1.5 exporter: use publish-snes-1.6.py for the current build'
OUT=ROOT/'evidence'
OUT.mkdir(exist_ok=True)
entries=[]

def normalize(value):
    if isinstance(value,dict): return {normalize(k):normalize(v) for k,v in value.items()}
    if isinstance(value,list): return [normalize(v) for v in value]
    if not isinstance(value,str): return value
    for old,new in ((str(ROOT),'<workspace>'),(ROOT.as_posix(),'<workspace>'),
                    (r'H:\DIIUM D-R35','<card-export>')):
        value=value.replace(old,new)
    return value

def publish(source,destination):
    source=ROOT/source; destination=ROOT/destination
    assert source.is_file(),source
    assert source.suffix.lower() not in ('.srm','.state','.so','.zip','.smc','.sfc'),source
    destination.parent.mkdir(parents=True,exist_ok=True)
    raw=source.read_bytes()
    if source.suffix=='.json':
        output=(json.dumps(normalize(json.loads(raw)),indent=2)+'\n').encode()
    elif source.suffix in ('.txt','.log','.asm','.h','.md','.jsonl'):
        output=normalize(raw.decode('utf-8')).replace('\r\n','\n').encode()
    else:
        output=raw
    destination.write_bytes(output)
    entries.append({'source':str(source.relative_to(ROOT)).replace('\\','/'),
                    'published':str(destination.relative_to(ROOT)).replace('\\','/'),
                    'source_sha256':sha256(raw).hexdigest(),
                    'published_sha256':sha256(output).hexdigest(),
                    'bytes':len(output),'normalized':output!=raw})

groups={
 'hardware-inventory-return-20261004T180435Z':('review.txt','analysis.json','device-tree.json','device-tree.dtb','hardware_probe_v1.jsonl'),
 'hardware-runtime-return-20261004T182651Z':('review.txt','analysis.json','hardware_probe_v2.jsonl','kernel_log-0.491.txt','kernel_log-105.222.txt','kernel_symbols-0.481.txt'),
 'hardware-console-return-20261004T185838Z':('review.txt','analysis.json','comparison-v2.json','cleanup-verification.json'),
 'hardware-architecture-review':('review.txt','driver-dwarf.json','abi-resolution.json','abi-assembly.txt','neon-code-census.json','kernel-module-map.json'),
 'launcher-performance-review':('review.txt','annotated-paths.txt'),
 'v9-render-return-20261004T164007Z':('analysis.json','emu_sfc_plus_v9_render_test.txt'),
 'v10-budget-return-20261004T170305Z':('analysis.json',),
}
for directory,names in groups.items():
    for name in names:
        publish(Path('device-evidence')/directory/name,Path('evidence/2026-10-04')/directory/name)

returns={
 'snes-mvp-return-20261004T203459Z':'snes-mvp-1.0',
 'snes-mvp-return-20261004T210409Z':'snes-mvp-1.1',
 'snes-mvp-return-20261004T221027Z':'snes-mvp-1.2',
 'snes-mvp-return-20261004T222804Z':'snes-mvp-1.3',
 'snes-mvp-return-20261004T224312Z':'snes-mvp-1.4',
 'snes-mvp-return-20261004T232518Z':'snes-mvp-1.5',
}
for directory,label in returns.items():
    names=('review.txt','analysis.json','snes-mvp/startup.log','snes-mvp/startup-processes.txt',
           'snes-mvp/startup-platform.txt','snes-mvp/runtime-platform.txt',
           'snes-mvp/last-run.log','snes-mvp/saves/last-session.txt',
           'ReadJoystick.asm','ReadJoystickThread.asm','wdt.asm','power_key.asm',
           'joystick_input.asm','joystick_poll.asm','joy_key_mask.hex')
    for name in names:
        source=Path('device-evidence')/directory/name
        if (ROOT/source).is_file():
            publish(source,Path('evidence/2026-10-04')/label/Path(name).name)

for name in ('proposal.txt','hardware-notes.txt','runtime-notes.txt','core-notes.txt',
             'ps1-binary-census.json','ps1-core-inventory.json','ps1-annotated-paths.txt'):
    publish(Path('device-evidence/platform-redesign-review')/name,
            Path('docs/reference/platform-redesign')/name)

for name in ('verification.json','contracts.log','board-input-contract.log',
             'vendor-input-reference.log','vendor-input-reference.h','timing-contract.log',
             'startup-contract.log','wrapper-contract.log','abi-versions.txt','dependencies.txt'):
    publish(Path('build/snes-mvp/out')/name,Path('evidence/verification/snes-mvp-1.5')/name)
for name in ('smoke-final','paced-smoke'):
    publish(Path('build/snes-mvp/out')/name/'last-session.txt',
            Path('evidence/verification/snes-mvp-1.5')/(name+'-session.txt'))

release=ROOT/'releases/snes-mvp-1.5'; release.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'build/snes-mvp/out/snes-mvp',release/'snes-mvp')
shutil.copy2(ROOT/'build/snes-mvp/launch.sh',release/'launch.sh')
checks=json.loads((ROOT/'build/snes-mvp/out/verification.json').read_text())
assert sha256((release/'snes-mvp').read_bytes()).hexdigest()==checks['binary_sha256']
manifest={'version':'1.5','hardware_status':'directions, launcher/game/state confirmed; occasional lag and rare random crackles; full rendering not qualified',
          'binary_sha256':checks['binary_sha256'],
          'wrapper_sha256':sha256((release/'launch.sh').read_bytes()).hexdigest(),
          'verification':checks,'dependencies':'owner-supplied matched driver/core/runtime; no ROM/save provided'}
(release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for name,output in (('ui-library.png','launcher.png'),('ui-pause.png','pause.png')):
    target=ROOT/'docs/assets'/output; target.parent.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'build/snes-mvp'/name,target)
(OUT/'manifest.json').write_text(json.dumps({'as_of':'2026-10-04','entries':entries},indent=2)+'\n')
print(f'Published {len(entries)} selected artifacts and owned MVP release; private progress excluded')
