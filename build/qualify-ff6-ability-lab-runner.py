"""Load each new profile through the owned real runner/consuming-client seam."""
from pathlib import Path
from hashlib import sha256
import json, shutil, subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-ability-lab-private-v1'
CORE=ROOT/'build/confuser-gameplay-private-v1/plus-a7.so'
FIXTURE=ROOT/'build/combined-gameplay-private-v1/native-check'
ROM=ROOT/'build/plus-a7-out/ff6.sfc'
def digest(path):return sha256(path.read_bytes()).hexdigest()

analysis=json.loads((OUT/'analysis.json').read_text())
assert digest(CORE)==analysis['working_core_sha256'] and digest(ROM)==analysis['rom_sha256']
result=[]
for name in ('spellbook','skills','rage'):
    folder=OUT/('runner-'+name);assert not folder.exists();folder.mkdir()
    source=OUT/'playable'/name/'saves'
    for path in source.iterdir():shutil.copy2(path,folder/path.name)
    with (folder/'check.log').open('x') as log:
        subprocess.run(['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E',
            'LD_LIBRARY_PATH=build/sysroot/lib',str(FIXTURE.relative_to(ROOT)),
            str(ROM.relative_to(ROOT)),str(CORE.relative_to(ROOT)),str(folder.relative_to(ROOT))],
            cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    text=(folder/'check.log').read_text();assert 'two snapshot loads' in text and '120 full drawings' in text
    result.append({'profile':name,'two_loads_passed':True,'calls':120,
        'log_sha256':digest(folder/'check.log'),'a7_timing':False})
    print('PASS actual runner/PCM owner: two new '+name+' snapshot loads,120 drawings',flush=True)
record={'fixture_sha256':digest(FIXTURE),'core_sha256':digest(CORE),'rom_sha256':digest(ROM),
    'physical_hardware':False,'profiles':result,'calls':360,'snapshot_loads':6}
(OUT/'runner-proof.json').write_text(json.dumps(record,indent=2)+'\n')
