"""Exercise actual wrapper with independent splash/error/stall/live-write fixtures."""
from pathlib import Path
from hashlib import sha256
import json, os, subprocess, sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/a7-pair-private-v1'
q=json.loads((OUT/'verification.json').read_text());assert q['native_client_qualified']
# Only fixture path routing changes. All production launch/ownership logic stays.
s=(OUT/'launch.sh').read_text()
assert s.count('BASE=/usr/retro/snes-pair1')==s.count('TRIGGER=/usr/retro/snes-mvp')==1
s=s.replace('BASE=/usr/retro/snes-pair1','BASE=$D35_MVP_BASE').replace('TRIGGER=/usr/retro/snes-mvp','TRIGGER=$D35_MVP_BASE')
wrapper=OUT/'fixture-launch.sh';wrapper.write_text(s,newline='\n')
s=(ROOT/'build/snes-mvp/check-startup-wrapper.py').read_text().replace("base/'snes-mvp'","base/'pair-suite'")
anchor='    start=time.monotonic()'
assert s.count(anchor)==1
s=s.replace(anchor,"    (base/'owner.rom').write_text('fixture owner ROM')\n    (base/'ROM-PATH.txt').write_text(str(base/'owner.rom')+'\\n')\n"+anchor)
fixture=OUT/'wrapper-check.py';fixture.write_text(s,newline='\n')
log=OUT/'wrapper-check.log'
with log.open('w') as f:
    subprocess.run([sys.executable,str(fixture),str(OUT/'wrapper-fixtures')],env={**os.environ,'D35_WRAPPER_UNDER_TEST':str(wrapper)},check=True,stdout=f,stderr=subprocess.STDOUT)
assert 'zero diagnostic card writes or global sync during ready child' in log.read_text()
q['wrapper_qualified']=True;q['proof_hashes'][log.name]=sha256(log.read_bytes()).hexdigest()
for p in (Path(__file__),ROOT/'build/snes-mvp/check-startup-wrapper.py'):
    q['source_hashes'][p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
q['checks'].append('actual one-shot wrapper: early error, PCM failure, startup timeout, ready session, unarmed boot, splash exit/stall/zombie; no live-child card writes or global sync')
(OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
print('PASS: one-shot wrapper and exclusive display handoff; no live-child card logging')
