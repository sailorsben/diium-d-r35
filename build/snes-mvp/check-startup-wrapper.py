"""Run the shipped shell wrapper against exiting, stuck and ready processes."""
from pathlib import Path
import os
import subprocess
import sys
import time
import threading
import shutil

source=Path(__file__).with_name('launch.sh')
root=Path(sys.argv[1]).resolve()
root.mkdir(parents=True,exist_ok=True)
def run(name, body, expected, ready=False, armed=True, splash=None):
    base=root/name
    base.mkdir(exist_ok=True)
    (base/'snes-mvp').write_text('#!/bin/sh\n'+body+'\n')
    (base/'snes-mvp').chmod(0o755)
    if armed: (base/'armed').write_text('fixture\n')
    # A returned run must not be mixed into the new diagnostic window.
    if name=='ready-session': (base/'runtime-platform.txt').write_text('stale previous snapshot\n')
    proc=base/'proc'; proc.mkdir(exist_ok=True)
    stop=base/'splash.stop'; ack=base/'splash.ack'; started=base/'child-started'
    for path in (stop,ack,started):
        if path.exists(): path.unlink()
    worker=None
    observed=[]
    if name=='ready-session':
        def observe_before_exit():
            deadline=time.monotonic()+4
            while time.monotonic()<deadline:
                progress=base/'last-progress.txt'
                if progress.exists() and 'fixture-running-37' in progress.read_text():
                    observed.append(True);return
                time.sleep(.03)
        observer=threading.Thread(target=observe_before_exit)
        observer.start()
    if splash:
        entry=proc/'321'; entry.mkdir(exist_ok=True)
        (entry/'comm').write_text('showlogo\n')
        (entry/'status').write_text('State:\tS (sleeping)\n')
        if splash=='exits':
            def vendor_splash():
                deadline=time.monotonic()+6
                while not stop.exists() and time.monotonic()<deadline: time.sleep(.02)
                assert stop.exists(), 'Launcher never sent vendor splash stop marker'
                assert not started.exists(), 'MVP opened while splash still owned display'
                time.sleep(.25)
                assert not started.exists(), 'MVP raced splash cleanup'
                ack.write_text('released\n')
                shutil.rmtree(entry)
            worker=threading.Thread(target=vendor_splash)
            worker.start()
    env=dict(os.environ,D35_MVP_BASE=str(base),D35_MVP_STARTUP_SECONDS='2',
             D35_MVP_PROC_ROOT=str(proc),D35_MVP_SPLASH_STOP=str(stop),D35_MVP_SPLASH_ACK=str(ack))
    (base/'snes-mvp').write_text('#!/bin/sh\n: > "'+str(started)+'"\n'+body+'\n')
    start=time.monotonic()
    result=subprocess.run(['sh',str(source)],env=env,timeout=12,capture_output=True,text=True)
    if worker:
        worker.join(timeout=1)
        assert not worker.is_alive()
    assert result.returncode==expected,(name,result.returncode,result.stderr)
    if not armed:
        assert not (base/'startup.log').exists()
        return
    assert not (base/'armed').exists() and (base/'last-launch').exists()
    log=(base/'startup.log').read_text()
    if splash=='stuck':
        assert 'splash handoff timeout' in log and not started.exists(),log
        shutil.rmtree(proc/'321')
        print('PASS: splash timeout refuses to start competing MVP display owner')
        return
    assert 'splash handoff complete active_pids=none' in log,log
    if splash=='exits':
        assert ack.exists() and started.exists()
        assert log.index('splash handoff complete')<log.index('child pid='),log
    assert f'ready={"yes" if ready else "no"}' in log,log
    if name=='stalled':
        assert 'STARTUP TIMEOUT' in log
        stall=(base/'startup-stall.txt').read_text()
        assert 'Task ' in stall and 'wchan' in stall
        assert 'fixture stall' in (base/'last-run.log').read_text()
    else:
        assert 'STARTUP TIMEOUT' not in log
    if name=='ready-session':
        elapsed=time.monotonic()-start
        observer.join(timeout=1)
        assert observed,'Progress was not persisted while the child was still alive'
        assert 5<=elapsed<9, f'Cancelled monitor left a sleeper or limited ready session: {elapsed}'
        runtime=(base/'runtime-platform.txt').read_text()
        assert 'Runtime snapshot child=' in runtime and 'Task ' in runtime,runtime
        assert 'stale previous snapshot' not in runtime
        assert 'fixture ready runtime' in (base/'last-run.log').read_text()
        assert 'fixture-running-37' in (base/'last-progress.txt').read_text()
        assert (base/'runtime-platform-latest.txt').stat().st_size>0
        assert 'end_after_sync_uptime=' in (base/'diagnostic-flush.log').read_text()
        print('PASS: diagnostic progress persisted before child exit; bounded live/kernel snapshots and flush timing retained')
    print(f'PASS: startup wrapper {name}, exit={result.returncode}, ready={ready}')

run('early-error','printf "fixture early error\\n"; exit 7',7)
run('stalled','printf "fixture stall\\n"; exec sleep 60',143)
run('ready-session',': > "$D35_MVP_READY_FILE"; printf "fixture ready runtime\\n"; printf "fixture-running-37\\n" > "$D35_MVP_PROGRESS_FILE"; sleep 5; exit 0',0,ready=True)
run('unarmed','exit 99',0,armed=False)
run('splash-handoff',': > "$D35_MVP_READY_FILE"; exit 0',0,ready=True,splash='exits')
run('splash-stalled','exit 99',1,splash='stuck')
print('PASS: unarmed boot skips MVP; startup deadline does not limit a ready session')
