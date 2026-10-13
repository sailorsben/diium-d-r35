"""New fixed-color mechanism across 406 known animations, bounded offline only."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from hashlib import sha256
import json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fixed-rows-private-v3'
SCREEN=ROOT/'build/ff6-effect-screen-private-v1'
CORE=OUT/'counted-core/snes9x2005_plus_libretro.so'

def run(index):
    log=OUT/f'screen/{index:03d}.log'
    assert not log.exists()
    with log.open('x') as f:
        p=subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),
            str(SCREEN/'screen'),str(ROOT/'build/plus-a7-out/plus-a7.so'),str(CORE),
            str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/'build/magitek-bio-private/scene.state'),
            '600','magitek-bio',str(index)],cwd=ROOT,env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},
            stdout=f,stderr=subprocess.STDOUT,timeout=180)
    text=log.read_text();passed=p.returncode==0 and 'PASS: 600 frames exact visible pixels' in text
    identity='IDENTITY init_hits=' in text
    print(index,passed,identity,flush=True)
    return {'index':index,'calls':600,'exact_output_pass':passed,'identity_verified':identity,
            'exit_code':p.returncode,'log_sha256':sha256(log.read_bytes()).hexdigest()}

if __name__=='__main__':
    assert not (OUT/'screen').exists();(OUT/'screen').mkdir()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=[f.result() for f in as_completed([pool.submit(run,i) for i in range(406)])]
    receipt={'results':sorted(results,key=lambda r:r['index']),'core_sha256':sha256(CORE.read_bytes()).hexdigest(),
        'passed':all(r['exact_output_pass'] and r['identity_verified'] for r in results),
        'context':'14-byte animation overlay in both cores; original Bio Blast mechanics and single-enemy target',
        'A7_performance_evidence':False,'universal_coverage':False,'card_writes':0}
    (OUT/'screen.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert receipt['passed']
