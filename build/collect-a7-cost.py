"""Archive complete measurement return plus all private progress; card writes0."""
from pathlib import Path
from hashlib import sha256
import importlib.util, json, shutil, subprocess
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('cost_collect',ROOT/'build/collect-platform-lab.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
card=Path('D:/');source=card/'retro/snes-cost1';assert source.is_dir()
archive=collector.collect(card);entries=[]
for p in sorted(source.rglob('*')):
    if not p.is_file():continue
    assert not p.is_symlink();name=p.relative_to(source);target=archive/'snes-cost1'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    before=sha256(p.read_bytes()).hexdigest();shutil.copy2(p,target)
    assert before==sha256(p.read_bytes()).hexdigest()==sha256(target.read_bytes()).hexdigest()
    entries.append({'path':name.as_posix(),'sha256':before,'bytes':p.stat().st_size})
r=subprocess.run(['chkdsk','D:'],capture_output=True,text=True)
(archive/'chkdsk-cost-return.txt').write_text(r.stdout,encoding='utf-8')
assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
identity=json.loads((source/'suite-identity.json').read_text())
for name,key in [('unit-suite','suite_sha256'),('measure-core.so','core_sha256'),('replay.state','state_sha256')]:assert sha256((source/name).read_bytes()).hexdigest()==identity[key]
assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
expected=b'SNES-cost1 diagnostic measurement suite; baseline renderer only; no production candidate\n'
assert (source/'last-launch').read_bytes()==expected
(archive/'cost-collection.json').write_text(json.dumps({'card_writes':0,'files':entries,'identity_verified':True,'clean_fat':True,'marker_consumed':True},indent=2)+'\n')
print(archive)
