"""Exact original-ROM casts; identity and animation completion are mandatory."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-effect-screen-private-v1/natural'
Q=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib']
def run(case):
    index=case['index'];log=OUT/f'{index:03d}.log';assert not log.exists()
    with log.open('x') as f:
        p=subprocess.run(Q+[str((OUT/'screen').relative_to(ROOT)),
            'build/plus-a7-out/plus-a7.so',str((OUT/'core/snes9x2005_plus_libretro.so').relative_to(ROOT)),
            'build/plus-a7-out/ff6.sfc',str((OUT/f'select-{index}/scene.state').relative_to(ROOT)),
            '1200','magitek-bio',str(index)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=180)
    assert p.returncode==0,(index,p.returncode)
    text=log.read_text();assert 'PASS: 1200 frames exact visible pixels' in text and 'deinit_hits=' in text
    print(f"PASS normal {case['name']}:1200 comparisons, actual init/deinit",flush=True)
with ThreadPoolExecutor(max_workers=2) as pool:
    for future in as_completed([pool.submit(run,c) for c in json.loads((OUT/'cases.json').read_text())]):future.result()
