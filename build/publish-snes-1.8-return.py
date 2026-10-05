"""Publish selected crashed1.8 return and source-fix checks, never private progress."""
from pathlib import Path
from hashlib import sha256
import argparse,json
ROOT=Path(__file__).resolve().parent.parent

def publish(archive):
    archive=archive.resolve();archive.relative_to(ROOT/'device-evidence')
    collection=json.loads((archive/'collection.json').read_text())
    assert collection['card_writes']==0 and not collection['armed_present']
    for entry in collection['copied_and_hash_verified']:
        assert sha256((archive/entry['archive_path']).read_bytes()).hexdigest()==entry['sha256']
    analysis=json.loads((archive/'analysis.json').read_text())
    followup=json.loads((archive/'observation-followup.json').read_text())
    assert followup['shutdown_observation']=='whole device powered off'
    assert analysis['version']=='1.8' and analysis['raw_fields']['phase']=='running'
    assert analysis['returned_owned_files_match_release'] and analysis['stock_binaries_unchanged']
    assert analysis['preexisting_private_files_changed']==0
    manifest_path=ROOT/'evidence/manifest.json';manifest=json.loads(manifest_path.read_text())
    for entry in manifest['entries']:
        assert sha256((ROOT/entry['published']).read_bytes()).hexdigest()==entry['published_sha256']
    prefix='evidence/2026-10-04/snes-mvp-1.8-return/'
    selected={archive/'analysis.json':prefix+'analysis.json',
              archive/'observation-followup.json':prefix+'observation-followup.json',
              archive/'snes-mvp/last-progress.txt':prefix+'last-progress.txt',
              archive/'snes-mvp/last-progress.previous':prefix+'last-progress.previous',
              archive/'snes-mvp/startup.log':prefix+'startup.log',
              archive/'snes-mvp/startup-platform.txt':prefix+'startup-platform.txt',
              archive/'snes-mvp/runtime-platform.txt':prefix+'runtime-platform.txt',
              archive/'snes-mvp/runtime-platform-latest.txt':prefix+'runtime-platform-latest.txt',
              archive/'snes-mvp/diagnostic-flush.log':prefix+'diagnostic-flush.log',
              archive/'snes-mvp/kernel-tail.txt':prefix+'kernel-tail.txt',
              archive/'snes-mvp/last-run.log':prefix+'last-run.log',
              ROOT/'build/snes-mvp/out/wrapper-no-sed-contract.log':'evidence/verification/snes-mvp-unreleased/wrapper-no-sed-contract.log',
              ROOT/'build/snes-mvp/out/publication-guard-contract.log':'evidence/verification/snes-mvp-unreleased/publication-guard-contract.log',
              ROOT/'build/snes-mvp/out/1.8-return-extended-equivalence.log':prefix+'extended-equivalence.log'}
    assert 'PASS: 10000 frames exact visible pixels' in (ROOT/'build/snes-mvp/out/1.8-return-extended-equivalence.log').read_text()
    assert 'PATH lacking head and sed' in (ROOT/'build/snes-mvp/out/wrapper-no-sed-contract.log').read_text()
    entries=manifest['entries']
    for source,name in selected.items():
        raw=source.read_bytes()
        output=raw.decode().replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
        target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==output,'Historical evidence must not be replaced'
        else:target.write_bytes(output)
        entry={'source':source.relative_to(ROOT).as_posix(),'published':name,
               'source_sha256':sha256(raw).hexdigest(),'published_sha256':sha256(output).hexdigest(),
               'bytes':len(output),'normalized':raw!=output}
        old=[e for e in entries if e['published']==name]
        if old:assert old==[entry]
        else:entries.append(entry)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Published {len(selected)} return/source-check artifacts; {len(entries)} total; shipped1.8 unchanged')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive',type=Path)
    publish(parser.parse_args().archive)
