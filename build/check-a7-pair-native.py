"""Qualify actual diagnostic client against independent consuming PCM fixture."""
from pathlib import Path
from hashlib import sha256
import json, os, subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/a7-pair-private-v1'
q=json.loads((OUT/'verification.json').read_text());assert q['passed']
s=(ROOT/'build/snes-mvp/native-runner-check.c').read_text()
s=s[:s.index('static int native_menu(')].replace('menu_visits,menu_action,next_menu,deficit_mode','menu_visits,next_menu,deficit_mode')
body=(ROOT/'build/a7-cost-native-check.c').read_text()
body=body.replace('D35_COST_STATE','D35_PAIR_STATE')
body=body.replace('    assert(!setenv("D35_COST_MODE","0",1));','    assert(!setenv("D35_PAIR_START","0",1));\n    assert(!setenv("D35_PAIR_LIMIT","120",1));')
body=body.replace('    assert(!setenv("D35_COST_CONTRACT_FIXTURE","1",1));','')
p=OUT/'runner/pair-native-check.c';p.write_text(s+'\n'+body,newline='\n')
libraries=['-L'+str(ROOT/'build/sysroot/lib'),'-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
subprocess.run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-no-pie','-nostdlib','-I'+str(ROOT/'build/snes9x2005/libretro-common/include'),'/usr/arm-linux-gnueabihf/lib/crt1.o',str(p),str(ROOT/'build/glibc230-stat-compat.c'),*libraries,'-o',str(OUT/'pair-native-check')],check=True)
for label in ('baseline','combined'):
    capture=OUT/f'native-{label}';capture.mkdir(exist_ok=False)
    log=OUT/f'native-{label}.log'
    with log.open('w') as f:
        subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'pair-native-check'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(OUT/f'{label}.so'),str(OUT/f'{label}-0.state'),str(capture)],env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},check=True,stdout=f,stderr=subprocess.STDOUT)
    assert 'PASS: consuming native provider' in log.read_text()
    q['proof_hashes'][log.name]=sha256(log.read_bytes()).hexdigest()
for path in (Path(__file__),p,ROOT/'build/a7-cost-native-check.c',ROOT/'build/snes-mvp/native-runner-check.c'):
    q['source_hashes'][path.relative_to(ROOT).as_posix()]=sha256(path.read_bytes()).hexdigest()
q['checks'].append('both cores through actual diagnostic native client: injected EBADFD, deferred flush after join, clean 120-frame independent retry/drain, sustained deficit rejected without hidden reprime')
q['native_client_qualified']=True
(OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
print('PASS: native consuming/fault/drain/deficit contracts for both isolated cores')
