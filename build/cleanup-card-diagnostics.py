from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import shutil
import json
import re

root=Path(__file__).resolve().parent.parent
retro=Path('D:/retro').resolve()
assert retro==Path('D:/retro').resolve() and (retro/'vrtemu').is_file()
pattern=re.compile(r'emu_sfc_(?:plus_v[1-7](?:_(?:audio|capture|timing|write_audit))?|compat_v[12]|pace_v2|probe_v1|timingfix_v1)\.(?:log|wav|txt)(?:\.tmp)?$')
targets=[p for p in retro.iterdir() if p.is_file() and pattern.fullmatch(p.name)]
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
archive=root/'device-evidence'/('card-cleanup-'+stamp)
archive.mkdir(parents=True,exist_ok=False)
def digest(p): return sha256(p.read_bytes()).hexdigest()
report=[]
for p in targets:
    resolved=p.resolve()
    assert resolved.parent==retro and pattern.fullmatch(resolved.name)
    dest=archive/p.name
    shutil.copy2(resolved,dest)
    checksum=digest(resolved)
    assert digest(dest)==checksum
    report.append({'name':p.name,'bytes':p.stat().st_size,'sha256':checksum})
    resolved.unlink()
(archive/'cleanup-manifest.json').write_text(json.dumps({'removed_from_card':report,
    'scope':'Only superseded emulator diagnostic logs/captures; archived and hash-verified first.'},indent=2)+'\n')
print(json.dumps({'archived_to':str(archive),'files_removed':len(report),
                  'bytes_removed':sum(p['bytes'] for p in report),'names':[p['name'] for p in report]},indent=2))
