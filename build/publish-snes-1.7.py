"""Publish the logging retry; retain the failed 1.6 release and all old evidence."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
checks=json.loads((ROOT/'build/snes-mvp/out/verification.json').read_text())
assert checks['passed'] and checks['version']=='1.7'
manifest_path=ROOT/'evidence/manifest.json';manifest=json.loads(manifest_path.read_text())
prefix='evidence/verification/snes-mvp-1.7/'
entries=[e for e in manifest['entries'] if not e['published'].startswith(prefix)]
for e in entries:assert sha256((ROOT/e['published']).read_bytes()).hexdigest()==e['published_sha256']
def publish(source,name):
    source=ROOT/source;raw=source.read_bytes()
    if name=='verification.json':
        data=json.loads(raw);data.pop('qualified_snapshot_sha256',None)
        output=(json.dumps(data,indent=2)+'\n').encode()
    else:output=raw.decode().replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
    target=ROOT/prefix/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(output)
    entries.append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
                    'source_sha256':sha256(raw).hexdigest(),'published_sha256':sha256(output).hexdigest(),
                    'bytes':len(output),'normalized':raw!=output})
for name in ('verification.json','contracts.log','display-queue-contract.log','startup-contract.log',
             'wrapper-contract.log','board-input-contract.log','timing-contract.log','platform-contract.log',
             'abi-versions.txt','dependencies.txt','diagnostic-crash.log'):
    publish(Path('build/snes-mvp/out')/name,name)
for folder,name in (('smoke-final','smoke-session.txt'),('paced-smoke','paced-session.txt')):
    publish(Path('build/snes-mvp/out')/folder/'last-session.txt',name)
release=ROOT/'releases/snes-mvp-1.7';release.mkdir(parents=True,exist_ok=True)
for source,name,key in ((ROOT/'build/snes-mvp/out/snes-mvp','snes-mvp','binary_sha256'),
                        (ROOT/'build/snes-mvp/launch.sh','launch.sh','wrapper_sha256')):
    assert sha256(source.read_bytes()).hexdigest()==checks[key];shutil.copy2(source,release/name)
meta={k:v for k,v in checks.items() if k!='qualified_snapshot_sha256'}
meta['dependencies']='Same locally built A7 core and owner-supplied matched driver/runtime; no private game data or dependencies published'
(release/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
manifest['entries']=entries;manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Published 1.7 diagnostics and owned release; {len(entries)} selected artifacts; historical releases preserved')
