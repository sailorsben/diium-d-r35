"""New archived failing contexts, existing renderer/checker; correctness only."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json,os,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def check(archive):
    archive=archive.resolve();out=archive/'ability-analysis/offline-contexts';assert not out.exists();out.mkdir()
    details=json.loads((archive/'ability-analysis/failure-analysis.json').read_text())['failures'];chosen={}
    for c in details:chosen.setdefault(c['observed_effect_id'],c)
    ref=ROOT/'build/plus-a7-out/plus-a7.so';candidate=ROOT/'build/ff6-effect-screen-private-v1/natural/core/snes9x2005_plus_libretro.so';runner=ROOT/'build/ff6-ability-lab-private-v1/check';rom=ROOT/'build/plus-a7-out/ff6.sfc'
    identities=json.loads((ROOT/'build/ff6-effect-screen-private-v1/final-identities.json').read_text())['payload_and_source_sha256']
    for p in (candidate,rom):assert digest(p)==identities[p.relative_to(ROOT).as_posix()]
    assert digest(ref)=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
    def run(c):
        n=c['case'];folder=archive/f'retro/snes-ability1/cases/{n:03d}';log=out/f'{n:03d}.log'
        with log.open('x') as stream:
            r=subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(runner),str(ref),str(candidate),str(rom),str(folder/'scene.state'),str(folder/'input.txt'),str(c['observed_effect_id']),'1200'],env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},stdout=stream,stderr=subprocess.STDOUT,timeout=120)
        text=log.read_text();record={'case':n,'effect':c['observed_effect_name'],'returncode':r.returncode,'passed':r.returncode==0,
            'calls':1200,'A7_performance_evidence':False,'log_sha256':digest(log),
            'identities':{p.relative_to(ROOT).as_posix():digest(p) for p in (runner,ref,candidate,rom,folder/'scene.state',folder/'input.txt')}}
        (out/f'{n:03d}.json').write_text(json.dumps(record,indent=2)+'\n');print(c['observed_effect_name'],r.returncode,flush=True);return record
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,chosen.values()))
    summary={'archived_failing_contexts':len(results),'exact_output_state_completed_contexts':sum(r['passed'] for r in results),'comparison_calls':sum(r['calls'] for r in results if r['passed']),
        'existing_generalized_renderer_checked':True,'new_core_builds':0,'card_writes':0,'A7_performance_evidence':False,'records':results}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');assert all(r['passed'] for r in results)
    print('PASS: archived failing contexts complete with exact graphics/PCM/state; QEMU is not A7 speed evidence')
if __name__=='__main__':check(Path(sys.argv[1]))
