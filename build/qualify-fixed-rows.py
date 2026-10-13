"""Independent original-core outputs and same-frame work counts; no A7 timing."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import csv,json,os,statistics,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fixed-rows-private-v3'
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',choices=('fixed-rows-private-v3','subscreen-rows-private-v1','dsp-dead-work-private-v1'),default=OUT.name)
    OUT=ROOT/'build'/parser.parse_args().out
BASE=ROOT/'build/ability-regression-private-v1'
RETURN=ROOT/'device-evidence/a7-pair-before-20261013T162915Z/retro/snes-ability2'

def digest(p):return sha256(p.read_bytes()).hexdigest()
def parse(p,prefix):return [list(map(int,s[len(prefix):].split(','))) for s in p.read_text().splitlines() if s.startswith(prefix)]

def qualify():
    assert not (OUT/'qualification.json').exists()
    plan=json.loads((BASE/'plan.json').read_text())
    reference=ROOT/'build/plus-a7-out/plus-a7.so'
    assert digest(reference)=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
    cores={'candidate':OUT/'plus-a7.so','fixed':OUT/'counted-core/snes9x2005_plus_libretro.so',
           'baseline':ROOT/'build/ff6-effect-screen-private-v1/natural/core/snes9x2005_plus_libretro.so'}
    logs=OUT/'exact';logs.mkdir(exist_ok=True)
    def run(job):
        c,label=job;log=logs/f"{c['seq']:03d}-{label}.log"
        # Reuse exactly qualified old census files instead of repeating them.
        old=BASE/f"census/{c['seq']:03d}-general.log"
        if not old.exists():old=ROOT/f"build/fixed-rows-private-v1/exact/{c['seq']:03d}-baseline.log"
        if label=='baseline' and old.exists():log=old
        if not log.exists():
            with log.open('x') as f:
                subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),
                    str(reference),str(cores[label]),str(ROOT/'build/plus-a7-out/ff6.sfc'),
                    str(BASE/f"cases/{c['seq']:03d}/scene.state"),str(BASE/f"cases/{c['seq']:03d}/input.txt"),
                    str(c['observed_effect_id']),'1200'],env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},
                    check=True,stdout=f,stderr=subprocess.STDOUT,timeout=180)
        assert 'PASS 1200 calls' in log.read_text()
        print(c['seq'],c['name'],label,'exact',flush=True)
        return {'case':c['seq'],'label':label,'log':str(log.relative_to(ROOT)),
                'sha256':digest(log),'core_sha256':digest(cores[label]),'calls':1200,'passed':True}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(run,[(c,label) for c in plan['cases'] for label in cores]))
    evidence=[]
    fields=('renderer_entries','tile_calls','clipped_calls','neon_rows','tile_decodes','palette_builds',
            'window1_left_flush','window1_right_flush','fixed_color_flush')
    for c in plan['cases']:
        def work(label):
            result=next(r for r in results if r['case']==c['seq'] and r['label']==label)
            data=parse(ROOT/result['log'],'WORK ')
            assert len(data)==1200 and [r[0] for r in data]==list(range(1200))
            return data
        before,after=work('baseline'),work('fixed')
        physical=list(csv.DictReader(s for s in (RETURN/f"run-{c['seq']:03d}/frames.csv").read_text().splitlines() if not s.startswith('#')))
        tail=[int(r['frame']) for r in physical[-17:-1]]
        def means(data):return {k:statistics.mean(data[i][j+1] for i in tail) for j,k in enumerate(fields)}
        a,b=means(before),means(after)
        evidence.append({'case':c['seq'],'name':c['name'],'tail_frames':tail,'before':a,'after':b,
                         'removed':{k:a[k]-b[k] for k in fields},'A7_unit_prices_measured':False})
    receipt={'experiment':OUT.name,'passed':True,'case_count':18,'calls_per_case':1200,'results':results,
             'aligned_tail_work_census':evidence,'core_sha256':digest(cores['candidate']),
             'A7_saving_measured':False,'production_gate_passed':False,'QEMU_timings_used':False,
             'card_writes':0,'limitations':['Fixed-row envelope: Mode1 ordinary non-mosaic only; subscreen shortcut: active depth above1 only.',
                          'No physical savings or universal performance proof.']}
    (OUT/'qualification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS:18 counter-free exact replays;18 counted exact replays;aligned work census;no card writes')

if __name__=='__main__':qualify()
