"""Qualify emitted ARM code, real concurrent OSS owner and dlopen observation seam."""
from pathlib import Path
from hashlib import sha256
import csv
import importlib.util
import json
import os
import re
import shlex
import struct
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/platform-lab2-out'
BIN = OUT / 'platform-lab'
SOURCES = ['build/platform-lab2.c', 'build/platform-lab2-font.h', 'build/platform-lab2-driver-trace.c',
           'build/platform-lab2-fixture.c', 'build/platform-lab2-trace-fixture.c', 'build/platform-lab2-trace-driver.c',
           'build/build-platform-lab2.sh', 'build/launch-platform-lab2.sh', 'build/dispatch-platform-lab.sh',
           'build/check-platform-lab2.py', 'build/lab2-wrapper-check.py',
           *['build/snes-mvp/'+n for n in ('board.c','board.h','timing.c','timing.h','startup.c','startup.h','platform.c','platform.h','ui.c','ui.h')]]
FLAGS = '-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'.split()
LIBS = ['-L'+str(ROOT/'build/sysroot/lib'), '-Wl,--no-as-needed',
        *['-l:'+n for n in ('libdl-2.30.so','libpthread-2.30.so','librt-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]]
BASE = ['arm-linux-gnueabihf-gcc',*FLAGS,'-std=gnu99','-O2','-Wall','-Wextra','-Werror','-nostdlib']
QEMU = ['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),'-E','LD_LIBRARY_PATH='+str(ROOT/'build/sysroot/lib')]
def digest(p): return sha256(p.read_bytes()).hexdigest()
def records(p): return [dict(v.split('=',1) for v in shlex.split(s) if '=' in v) for s in p.read_text().splitlines()]
def run(cmd, **kwargs):
    result = subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=40,**kwargs)
    assert result.returncode==0, (cmd,result.returncode,result.stdout,result.stderr)
    return result
def golden(rate,total):
    result=bytearray(); ramp=rate//50
    def trunc(n,d): return (1 if n>=0 else -1)*(abs(n)//d)
    for at in range(total):
        v=((at*400)%rate)*2400//rate
        if v>1200: v=2400-v
        v-=600
        if at<ramp: v=trunc(v*at,ramp)
        remaining=total-at
        if remaining<ramp: v=trunc(v*remaining,ramp)
        if at==0 or at+1>=total: v=0
        result.extend(struct.pack('<hh',v,v))
    return bytes(result)

def check():
    hashes={p:digest(ROOT/p) for p in SOURCES}; binary=digest(BIN); stamp=str(time.time_ns())
    test=OUT/('check-'+stamp); test.mkdir()
    result=run(QEMU+[str(BIN),'--selftest']); (OUT/'selftest.log').write_text(result.stdout+result.stderr)
    smoke=test/'smoke'; smoke.mkdir()
    run(QEMU+[str(BIN),'--null','--quick','--supervise','--output',str(smoke)])
    data=records(smoke/'results.log')
    assert any(r['event']=='run_end' and r['status']=='complete' and r['issues']=='0' for r in data)
    timers=list(csv.DictReader((smoke/'timers.csv').open()))
    assert timers and {s['method'] for s in timers}=={'0','1','2','3'}
    assert all(int(s['end_ns'])>=int(s['begin_ns']) for s in timers)
    assert not any(r['event']=='controller_end' for r in data), 'Null must not fabricate hardware data'
    restore=next(r for r in data if r['event']=='timer_restore')
    assert restore['rc']=='0' and restore['original_ns']==restore['current_ns']
    core=['platform-lab2.c','platform-lab2-driver-trace.c','snes-mvp/board.c','snes-mvp/ui.c','snes-mvp/startup.c','snes-mvp/platform.c','snes-mvp/timing.c']
    fixture=test/'fixture'; fixture.mkdir(); exe=test/'oss-fixture'
    run(BASE+['-no-pie','/usr/arm-linux-gnueabihf/lib/crt1.o',*[str(ROOT/'build'/p) for p in core],
              str(ROOT/'build/platform-lab2-fixture.c'),'-Wl,--export-dynamic',
              *['-Wl,--wrap='+name for name in ('open','close','write','ioctl','poll')],*LIBS,'-o',str(exe)])
    run(QEMU+['-E','D35_LAB_FIXTURE_OUTPUT='+str(fixture),str(exe),'--null','--quick','--fixture-oss','--supervise','--output',str(fixture)])
    data=records(fixture/'results.log')
    controllers=[r for r in data if r['event']=='controller_end']
    assert len(controllers)==4 and all(r['complete']=='1' and r['error']=='0' and r['ring_bytes']=='0' for r in controllers),controllers
    assert all(r['submitted']==r['flipped']=='0' for r in controllers)
    for i,r in enumerate(controllers):
        producer=list(csv.DictReader((fixture/f'producer-{i}.csv').open()))
        assert len(producer)==int(r['frames']) and sum(int(s['samples']) for s in producer)==int(r['generated_frames'])
    assert any(r['name']=='GETTRIGGER' and r['rc']=='-1' for r in data if r['event']=='audio_capability')
    profiles=[32040,44100,32040,44100,44100,32040,32040,32040,44100]
    for i,rate in enumerate(profiles):
        actual=(fixture/f'fixture-{i}.s16').read_bytes()
        assert actual==golden(rate,rate//(8 if i<5 else 2)), (i,len(actual))
    audio=[]
    for p in fixture.glob('*.csv'):
        if p.name.startswith(('transport-','controller-')): audio.extend(csv.DictReader(p.open()))
    assert any(int(s['rc'])>0 and int(s['rc'])%4 for s in audio if s['operation']=='1')
    assert any(s['errno']=='11' for s in audio if s['operation']=='1')
    assert any(int(s['free_bytes'])<0 for s in audio if s['space_rc']=='0')
    stall=test/'stall'; stall.mkdir()
    result=subprocess.run(QEMU+[str(BIN),'--null','--fixture-stall','--deadline-ms','200','--supervise','--output',str(stall)],
                          cwd=ROOT,capture_output=True,text=True,timeout=8)
    assert result.returncode==72
    assert [r['action'] for r in records(stall/'results.log') if r['event']=='deadline']==['term','kill']
    driver=test/'trace-driver.so'; trace_exe=test/'trace-check'; trace_csv=test/'trace.csv'
    run(BASE+['-fPIC','-shared',str(ROOT/'build/platform-lab2-trace-driver.c'),*LIBS,'-o',str(driver)])
    run(BASE+['-no-pie','/usr/arm-linux-gnueabihf/lib/crt1.o',str(ROOT/'build/platform-lab2-trace-fixture.c'),
              str(ROOT/'build/platform-lab2-driver-trace.c'),'-Wl,--export-dynamic','-Wl,--wrap=syscall',*LIBS,'-o',str(trace_exe)])
    result=run(QEMU+[str(trace_exe),str(driver),str(trace_csv)])
    (OUT/'driver-trace-check.log').write_text(result.stdout+result.stderr)
    rows=list(csv.DictReader(s for s in trace_csv.read_text().splitlines() if not s.startswith('#')))
    assert len(rows)==8 and any(int(r['command'])==0x80045004 and r['argument']=='3000' for r in rows)
    assert any(int(r['command'])==0x80045005 and r['status']=='2' for r in rows)
    config=next(r for r in rows if int(r['command'])==0x40e45000)
    assert [int(config[k]) for k in ('input_addr','output_a','output_b')]==[0x1000,0x2000,0x3000]
    spec=importlib.util.spec_from_file_location('wrapper',ROOT/'build/lab2-wrapper-check.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    wrappers=module.check_wrapper(test/'wrapper')
    preview=OUT/'preview'; preview.mkdir(exist_ok=True)
    run(QEMU+[str(BIN),'--preview','--output',str(preview)])
    versions=re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text())
    assert versions and max((int(a),int(b)) for a,b in versions)<=(2,30)
    exports=run(['arm-linux-gnueabihf-readelf','--dyn-syms','-W',str(BIN)]).stdout
    assert all(re.search(r'GLOBAL\s+DEFAULT\s+\d+\s+'+name+r'\s*$',exports,re.M) for name in ('open','ioctl','close'))
    assert 'vst1.16' in (OUT/'disassembly.txt').read_text()
    assert binary==digest(BIN) and hashes=={p:digest(ROOT/p) for p in SOURCES}
    report={'passed':True,'hardware_qualified':False,'version':'lab2','binary_sha256':binary,'source_hashes':hashes,
            'checks':['native fractional PCM and ramp/stereo endpoints','actual ARM four timer methods and exact slack restoration',
                      'actual concurrent owner under odd-byte shorts, EAGAIN and misleading readiness',
                      'all nine accepted PCM streams equal independent Python waveform byte-for-byte',
                      'unsupported OSS query and negative free space retained','actual ARM stalled child TERM/KILL/reap',
                      'actual RTLD_LOCAL shared driver scalar/pointer/status syscall interception','GLIBC <=2.30 and exported observer',
                      'direct-resolution UI preview',*wrappers]}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': check()
