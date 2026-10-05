"""Publish selected 1.7 return evidence; keep all collected game progress private."""
from pathlib import Path
from hashlib import sha256
import argparse, json

ROOT=Path(__file__).resolve().parent.parent

def publish(archive):
    archive=archive.resolve()
    archive.relative_to(ROOT/'device-evidence')
    collection=json.loads((archive/'collection.json').read_text())
    assert collection['card_writes']==0 and not collection['armed_present']
    for entry in collection['copied_and_hash_verified']:
        assert sha256((archive/entry['archive_path']).read_bytes()).hexdigest()==entry['sha256']
    analysis=json.loads((archive/'analysis.json').read_text())
    assert analysis['version']=='1.7' and analysis['raw_fields']['phase']=='finished'
    assert analysis['returned_owned_files_match_release'] and analysis['stock_binaries_unchanged']
    manifest_path=ROOT/'evidence/manifest.json'
    manifest=json.loads(manifest_path.read_text())
    for entry in manifest['entries']:
        assert sha256((ROOT/entry['published']).read_bytes()).hexdigest()==entry['published_sha256']
    selected={'analysis.json':'analysis.json',
              'snes-mvp/saves/last-session.txt':'last-session.txt',
              'snes-mvp/last-progress.txt':'last-progress.txt',
              'snes-mvp/last-progress.previous':'last-progress.previous',
              'snes-mvp/startup.log':'startup.log',
              'snes-mvp/startup-platform.txt':'startup-platform.txt',
              'snes-mvp/runtime-platform.txt':'runtime-platform.txt',
              'snes-mvp/runtime-platform-latest.txt':'runtime-platform-latest.txt',
              'snes-mvp/diagnostic-flush.log':'diagnostic-flush.log',
              'snes-mvp/kernel-tail.txt':'kernel-tail.txt',
              'snes-mvp/last-run.log':'last-run.log'}
    entries=manifest['entries']
    for source_name,name in selected.items():
        source=archive/source_name
        target=ROOT/'evidence/2026-10-04/snes-mvp-1.7'/name
        raw=source.read_bytes()
        output=raw.decode('utf-8').replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==output,'Refusing to replace historical evidence'
        else:target.write_bytes(output)
        entry={'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
               'source_sha256':sha256(raw).hexdigest(),'published_sha256':sha256(output).hexdigest(),
               'bytes':len(output),'normalized':raw!=output}
        old=[e for e in entries if e['published']==entry['published']]
        if old:assert old==[entry]
        else:entries.append(entry)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Published {len(selected)} selected return artifacts; {len(entries)} total; private SRAM/snapshots stay local')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    publish(parser.parse_args().archive)
