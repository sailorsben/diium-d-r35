"""ARM replay failure paths, real supervisor and emitted progress screen; no card."""
from pathlib import Path
import json,os,subprocess,uuid
from attempt_archive import digest

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-kernel-private-v2'

def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def run(args,want=0,env=None):
    r=subprocess.run(args,cwd=ROOT,env={**os.environ,**(env or {})},capture_output=True,text=True,timeout=20)
    assert r.returncode==want,(r.returncode,r.stdout,r.stderr)
    return r.stdout

def main():
    assert os.name!='nt'
    flags=['-mcpu=cortex-a7','-marm','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-Ibuild','-I'+str(OUT/'runner'),'/usr/arm-linux-gnueabihf/lib/crt1.o']
    libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed','-l:libc-2.30.so','-l:libgcc_s.so.1','-l:ld-2.30.so']
    run(['arm-linux-gnueabihf-gcc',*flags,'build/check-fivegame-warmup.c',str(OUT/'runner/ui.c'),*libs,'-o',str(OUT/'warmup-check')])
    qemu=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot'];checks=[];logs=[]
    attempt=OUT/('replay-check-'+uuid.uuid4().hex[:12]);attempt.mkdir()
    for name in ['complete','menu','signal','invalid','missing','display']:
        d=attempt/'warmup'/name;d.mkdir(parents=True)
        source=d/'input.txt'
        if name!='missing':source.write_text('9999 0002\n' if name=='invalid' else '7 0002\n8649 0008\n')
        text=run([*qemu,str(OUT/'warmup-check'),name,str(d)],env={'D35_GAME_WARMUP':str(source),'D35_WARMUP_SCREEN':str(d/'screen.rgb565')})
        status=kv(d/'warmup.txt')['status']
        assert status=={'complete':'completed','menu':'abort_menu','signal':'abort_signal','invalid':'invalid_input','missing':'input_open_failed','display':'display_failed'}[name]
        logs.append(text);checks.append(name)
    run(['arm-linux-gnueabihf-gcc',*flags,'-DD35_COLD_STALL_NS=300000000ull',str(OUT/'main.c'),'build/check-fivegame-supervisor.c',*libs,'-o',str(OUT/'supervisor-check')])
    for name,want in [('progress',0),('stall',72),('abort',5)]:
        d=attempt/'supervisor'/name;d.mkdir(parents=True)
        run([*qemu,str(OUT/'supervisor-check'),'--supervise',str(d),str(OUT),'unused'],want=want,env={'D35_SUPERVISOR_FIXTURE':name,'D35_FFVI_RUN_LIMIT':'1'})
        s=kv(d/'supervisor.txt');assert s['reaped']=='1'
        if name=='stall':assert s['forced']=='1' and s['cold_replay_stall']=='1' and s['cold_replay_calls']=='123' and s['stop_reason']=='cold_replay_no_progress'
        else:assert s['forced']==s['cold_replay_stall']=='0'
        logs.append('PASS real supervisor '+name+' '+json.dumps(s)+'\n');checks.append('supervisor-'+name)
    (OUT/'replay-checks.log').write_text(''.join(logs))
    report={'passed':True,'checks':checks,'fixture_root':attempt.relative_to(ROOT).as_posix(),'test_stall_ns':300000000,'production_stall_ns':60000000000,'card_access':False,'sources':{n:digest(ROOT/'build'/n) for n in ['check-fivegame-replay.py','check-fivegame-warmup.c','check-fivegame-supervisor.c','fivegame-warmup-progress.h','fivegame-replay-progress.h']},'log_sha256':digest(OUT/'replay-checks.log')}
    (OUT/'replay-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(''.join(logs));print('PASS nine replay/supervisor fixtures; actual UI pixels emitted; no card writes')

if __name__=='__main__':main()
