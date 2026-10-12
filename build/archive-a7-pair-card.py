"""Strict private archive of every retro file, before any measurement write."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json, shutil, subprocess
ROOT=Path(__file__).resolve().parent.parent
def digest(p): return sha256(p.read_bytes()).hexdigest()
def archive(card):
    card=card.resolve()
    assert str(card).lower() in ('i:/','i:\\'), 'Explicitly reassigned test card only'
    assert (card/'retro/snes-cost1/suite-identity.json').is_file()
    out=ROOT/'device-evidence'/('a7-pair-before-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    out.mkdir(parents=True,exist_ok=False)
    entries=[]
    for p in sorted((card/'retro').rglob('*')):
        if not p.is_file(): continue
        assert not p.is_symlink()
        rel=p.relative_to(card);q=out/rel;q.parent.mkdir(parents=True,exist_ok=True)
        h=digest(p);shutil.copy2(p,q);assert digest(p)==digest(q)==h
        entries.append({'path':rel.as_posix(),'bytes':p.stat().st_size,'sha256':h})
    r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True)
    (out/'chkdsk-before.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
    assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
    assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
    (out/'archive.json').write_text(json.dumps({'card':'I:','all_retro_files':entries,'card_writes':0,'fat_clean':True},indent=2)+'\n')
    print(out)
    return out
if __name__=='__main__': archive(Path('I:/'))
