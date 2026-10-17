"""Exact ARM twenty-epoch oracle, native PCM and kernel-wrapper qualification."""
from pathlib import Path
import csv,json,os,re,subprocess,sys,shlex,uuid
from attempt_archive import digest

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-kernel-private-v2'

def kv(path):return dict(l.split('=',1) for l in path.read_text().splitlines() if '=' in l)
def run(args,name,env=None,timeout=120,want=0):
    with (OUT/name).open('w') as f:
        p=subprocess.run(args,cwd=ROOT,env={**os.environ,**(env or {})},stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    assert p.returncode==want,(name,p.returncode,(OUT/name).read_text()[-2400:])
    return (OUT/name).read_text()

def main():
    assert os.name!='nt' and not (OUT/'qualification.json').exists()
    prep=json.loads((OUT/'replay-preparation.json').read_text())
    for n,h in prep['frozen_payloads'].items():assert digest(OUT/n)==h,n
    rt=OUT/'runner'
    flags=['-DD35_PLUS_A7','-DD35_NATIVE_PCM','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-D_TIME_BITS=32','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O3','-flto=4','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-Ibuild','-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o']
    libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
    reuse='--reuse-measured' in sys.argv
    if reuse:
        sealed=json.loads((OUT/'measured-rehearsal.json').read_text())
        for n,h in sealed['files'].items():assert digest(ROOT/n)==h,n
    else:
        run(['arm-linux-gnueabihf-gcc',*flags,str(OUT/'main.c'),*[str(rt/n) for n in ('board.c','runner.c','audio-owner.c','native-pcm.c','startup.c','platform.c','timing.c','ui.c')],'build/glibc230-stat-compat.c',*libs,'-o',str(OUT/'fivegame-suite')],'build.log')
    abi=(OUT/'abi.txt').read_text() if reuse else run(['arm-linux-gnueabihf-readelf','-V',str(OUT/'fivegame-suite'),str(OUT/'plus-a7.so')],'abi.txt')
    assert all(tuple(map(int,m))<=(2,30) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',abi))
    qemu=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib']
    mock=OUT/'mock'
    env={'D35_ABILITY_MOCK':'1','D35_MVP_NO_PACING':'1','D35_FULL_HOST_FIXTURE':'1','D35_FIVE_ORACLE':'1'}
    if not reuse:
        mock.mkdir();print('Built ARM controller; running all twenty exact gameplay/oracle epochs',flush=True)
        run([*qemu,str(OUT/'fivegame-suite'),'--supervise',str(mock),str(OUT),'unused'],'mock.log',env,1800)
    plan=json.loads((OUT/'plan.json').read_text());checked=[]
    for row in plan['runs']:
        d=mock/f"run-{row['run']:03d}";s=kv(d/'last-session.txt');a=kv(d/'input.csv');head=kv(d/'headroom.txt')
        frames=list(csv.DictReader(l for l in (d/'frames.csv').read_text().splitlines() if not l.startswith('#')))
        assert s['runs']==s['rendered_frames']==s['video_submitted']=='1200' and s['presentation_skipped']=='0' and not s['error'],(row,s.get('error'))
        assert len(frames)==1200 and a['#oracle_checks']=='1200' and a['#oracle_enabled']=='1'
        assert int(s['presentation_policy'])==row['policy'] and kv(d/'result.txt')['runner_rc']=='0'
        assert s['audio_remaining_frames']==s['audio_cleared_frames']=='0'
        assert int(s['output_accepted_frames_including_priming'])==int(s['resampled_enqueued_frames'])+int(s['priming_silence_frames'])
        pcm=kv(d/'pcm-full.txt');assert pcm['retained_from']=='0' and not pcm['failure'] and head['physical']=='0'
        assert int(head['period_ns'])==round(1e9/plan['cases'][row['fixture']]['fps'])
        if row['fixture']==3:
            warm=kv(d/'warmup.txt');assert warm['cold_boot_calls']=='8656' and warm['status']=='completed' and warm['measured_metrics_reset_before_audio']=='1'
        assert (d/'end-state.bin').stat().st_size>300000
        checked.append({**row,'calls':1200,'exact_original_gameplay_pixels_PCM_samples':True,'warmup_calls':8656 if row['fixture']==3 else 0})
    assert kv(mock/'suite-result.txt')['runs']=='20'
    supervisor=kv(mock/'supervisor.txt');assert supervisor['forced']=='0' and supervisor['reaped']=='1' and supervisor['cold_replay_stall']=='0'
    assert supervisor['cold_replay_calls']=='8656' and supervisor['cold_replay_epoch']=='16'
    print('PASS 24000 exact measured pixel/PCM/sample-count calls and 34624 cold replay calls',flush=True)
    # Reuse the independent consuming provider with this exact rebuilt runner.
    native_flags=[v for v in flags if v!='-flto=4']+['-O2']
    if not reuse:run(['arm-linux-gnueabihf-gcc',*native_flags,str(rt/'fivegame-native-check.c'),str(rt/'ui.c'),'build/glibc230-stat-compat.c',*libs,'-o',str(OUT/'native-check')],'native-build.log')
    for policy in ('0','1'):
        d=OUT/('native-'+policy)
        if reuse:text=(OUT/('native-'+policy+'.log')).read_text()
        else:
            d.mkdir()
            text=run([*qemu,str(OUT/'native-check'),str(OUT/'cases/000/game.sfc'),str(OUT/'plus-a7.so'),str(OUT/'cases/000/scene.state'),str(d)],'native-'+policy+'.log',{'D35_FULL_HOST_FIXTURE':'1','D35_PRESENTATION_POLICY':policy,'D35_ABILITY_INPUT':str(OUT/'cases/000/input.txt'),'D35_ABILITY_EXPECTED':str(OUT/'cases/000/expected.bin')},180)
        assert 'PASS: consuming native provider' in text
    print('PASS consuming native PCM both policies, busy-credit/fault/drain/deficit controls',flush=True)
    shell=['qemu-arm','-0','busybox','-L','build/sysroot','build/uart-fix-private/firmware-busybox','sh']
    run(shell+['-n',str(OUT/'launch.sh')],'wrapper-syntax.log');checks=[]
    wrapper_root=OUT/('wrapper-'+uuid.uuid4().hex[:12])
    for name in ['normal','module_endpoint','loaded_module','observer_before','observer_after','active_splash','child139','forced72']:
        d=wrapper_root/name;d.mkdir(parents=True);(d/'mvp').mkdir();(d/'proc').mkdir();(d/'sys').mkdir()
        for p in [d/'armed',d/'mvp/armed']:p.write_bytes(b'fixture\n')
        (d/'ROM-PATH.txt').write_text(str(OUT/'cases/000/game.sfc')+'\n')
        (d/'uart-observe').write_text('#!/bin/sh\ncase "$2" in *uart-before) [ "'+name+'" = observer_before ] && exit 1;; *uart-after) [ "'+name+'" = observer_after ] && exit 1;; esac\nmkdir "$2"\n')
        code=139 if name=='child139' else 72 if name=='forced72' else 0
        (d/'fivegame-suite').write_text('#!/bin/sh\nprintf executed > '+shlex.quote(str(d/'executed'))+'\nexit '+str(code)+'\n')
        for p in [d/'uart-observe',d/'fivegame-suite']:p.chmod(0o755)
        if name=='module_endpoint':(d/'proc/d35_uart_tx').write_text('old endpoint')
        if name=='loaded_module':(d/'sys/module/d35_uart_tx').mkdir(parents=True)
        if name=='active_splash':
            (d/'proc/123').mkdir();(d/'proc/123/comm').write_text('showlogo\n');(d/'proc/123/status').write_text('State:\tS\n')
        args=['env','D35_LAB_BASE='+str(d),'D35_MVP_BASE='+str(d/'mvp'),'D35_LAB_PROC_ROOT='+str(d/'proc'),'D35_LAB_SYS_ROOT='+str(d/'sys'),'D35_LAB_SPLASH_STOP='+str(d/'stop'),*shell,str(OUT/'launch.sh')]
        blocked=name in ['child139','forced72'];want=124 if blocked else 0 if name=='normal' else 1
        run((['timeout','2'] if blocked else [])+args,'wrapper-'+name+'.log',want=want,timeout=15)
        assert not (d/'armed').exists() and not (d/'mvp/armed').exists()
        assert (d/'executed').exists()==(name in ['normal','observer_after','child139','forced72'])
        if name=='normal':run(args,'wrapper-replay.log');assert len(list((d/'results').glob('run-*')))==1
        checks.append(name)
    for n,h in prep['frozen_payloads'].items():assert digest(OUT/n)==h,n
    names=[*prep['frozen_payloads'],'fivegame-suite','launch.sh','dispatch.sh','ROM-PATH.txt']
    sources=[ROOT/'build'/n for n in ['prepare-fivegame-replay.py','qualify-fivegame-replay.py','fivegame-warmup-progress.h','fivegame-replay-progress.h','glibc230-stat-compat.c']]+list(rt.glob('*.[ch]'))+[OUT/'main.c',*OUT.glob('*.h')]
    report={'version':'fivegame-kernel2','passed':True,'measurement_only':True,'production_gate':False,'target':prep['target'],'actual_epochs':checked,'native_policies':[0,1],'wrapper_checks':checks,'frozen_game_payloads':prep['frozen_payloads'],'sources':{p.relative_to(ROOT).as_posix():digest(p) for p in sources},'payload_hashes':{n:digest(OUT/n) for n in names},'measured_rehearsal_receipt_sha256':digest(OUT/'measured-rehearsal.json') if reuse else None,'QEMU_performance_evidence':False,'physical_result':'PENDING','no_full_backup':True}
    (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS replay-aware five-game controller and kernel wrapper; physical qualification pending',flush=True)

if __name__=='__main__':main()
