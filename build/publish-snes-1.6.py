"""Append selected1.6 verification; preserve historical evidence and releases."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
assert json.loads((ROOT/'build/snes-mvp/out/verification.json').read_text())['version']=='1.6', 'Historical publisher: use the current version publisher'
manifest_path=ROOT/'evidence/manifest.json';manifest=json.loads(manifest_path.read_text())
entries=[e for e in manifest['entries'] if not e['published'].startswith('evidence/verification/snes-mvp-1.6/')]
for entry in entries:
    assert sha256((ROOT/entry['published']).read_bytes()).hexdigest()==entry['published_sha256']
def publish(source,name):
    source=ROOT/source;destination=ROOT/'evidence/verification/snes-mvp-1.6'/name
    raw=source.read_bytes()
    if name=='verification.json':
        data=json.loads(raw);data.pop('qualified_snapshot_sha256',None)
        output=(json.dumps(data,indent=2)+'\n').encode()
    else:
        output=raw.decode().replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(output)
    entries.append({'source':source.relative_to(ROOT).as_posix(),'published':destination.relative_to(ROOT).as_posix(),
                    'source_sha256':sha256(raw).hexdigest(),'published_sha256':sha256(output).hexdigest(),
                    'bytes':len(output),'normalized':raw!=output})
for name in ('verification.json','contracts.log','display-queue-contract.log','startup-contract.log',
             'wrapper-contract.log','board-input-contract.log','timing-contract.log','platform-contract.log',
             'abi-versions.txt','dependencies.txt'):
    publish(Path('build/snes-mvp/out')/name,name)
for directory,name in (('smoke-final','smoke-session.txt'),('paced-smoke','paced-session.txt')):
    publish(Path('build/snes-mvp/out')/directory/'last-session.txt',name)
for name in ('kernel-check.log','equivalence.log','runner-integration.log'):
    publish(Path('build/plus-a7-out')/name,name)
checks=json.loads((ROOT/'build/snes-mvp/out/verification.json').read_text())
release=ROOT/'releases/snes-mvp-1.6';release.mkdir(parents=True,exist_ok=True)
for source,name in ((ROOT/'build/snes-mvp/out/snes-mvp','snes-mvp'),(ROOT/'build/snes-mvp/launch.sh','launch.sh')):
    shutil.copy2(source,release/name)
assert sha256((release/'snes-mvp').read_bytes()).hexdigest()==checks['binary_sha256']
meta={key:value for key,value in checks.items() if key!='qualified_snapshot_sha256'}
meta['wrapper_sha256']=sha256((release/'launch.sh').read_bytes()).hexdigest()
meta['dependencies']='Owner-supplied matched driver/runtime and locally built A7 core; no ROM, private state or core dependency published'
(release/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
manifest['entries']=entries;manifest['as_of']='2026-10-04 America/Chicago'
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Published1.6 verification and owned runner; {len(entries)} total selected artifacts; old releases preserved')
