from pathlib import Path
import os, shutil, signal, subprocess, threading, time
ROOT=Path(__file__).resolve().parent.parent

def check_wrapper(root):
    root.mkdir(); tools = root / 'tools'; tools.mkdir()
    for name in ('sh', 'mv', 'mkdir', 'sleep'):
        (tools / name).symlink_to(shutil.which(name))
    (tools / 'sync').write_text('#!/bin/sh\nexit 0\n'); (tools / 'sync').chmod(0o755)
    assert not (tools / 'head').exists() and not (tools / 'sed').exists()
    checks = []
    for case in ('unarmed', 'normal', 'zombie', 'splash_exit', 'splash_stall', 'deadline'):
        base = root / case; base.mkdir(); lab = base / 'lab'; lab.mkdir()
        mvp = base / 'mvp'; mvp.mkdir(); proc = base / 'proc'; proc.mkdir()
        (lab / 'launch.sh').write_bytes((ROOT / 'build/launch-platform-lab2.sh').read_bytes())
        started = lab / 'child-started'; stop = base / 'splash-stop'
        (lab / 'platform-lab').write_text('#!/bin/sh\n: > "' + str(started) + '"\nexit ' + ('72' if case == 'deadline' else '0') + '\n')
        (lab / 'platform-lab').chmod(0o755)
        (mvp / 'launch-game-1.8.sh').write_text('#!/bin/sh\n[ ! -f "$D35_MVP_BASE/armed" ] || : > "$D35_MVP_BASE/game-started"\n')
        if case != 'unarmed':
            (lab / 'armed').write_text('fixture'); (mvp / 'armed').write_text('fixture')
        entry = proc / '321'
        if case.startswith('splash_') or case == 'zombie':
            entry.mkdir(); (entry / 'comm').write_text('showlogo\n')
            (entry / 'status').write_text('State:\tZ (zombie)\n' if case == 'zombie' else 'State:\tS (sleeping)\n')
        env = dict(os.environ, PATH=str(tools), D35_LAB_BASE=str(lab),
                   D35_MVP_BASE=str(mvp), D35_LAB_PROC_ROOT=str(proc),
                   D35_LAB_SPLASH_STOP=str(stop))
        failure = []
        def release():
            try:
                until = time.monotonic() + 3
                while not stop.exists() and time.monotonic() < until: time.sleep(.02)
                assert stop.exists() and not started.exists()
                time.sleep(.2); assert not started.exists()
                shutil.rmtree(entry)
            except BaseException as e: failure.append(e)
        worker = threading.Thread(target=release) if case == 'splash_exit' else None
        if worker: worker.start()
        process = subprocess.Popen(['sh', str(ROOT / 'build/dispatch-platform-lab.sh')],
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        if case == 'deadline':
            until = time.monotonic() + 3
            while time.monotonic() < until:
                logs = list((lab / 'results').glob('*/wrapper.log'))
                if logs and 'reboot required' in logs[0].read_text(): break
                time.sleep(.02)
            assert process.poll() is None and logs and 'reboot required' in logs[0].read_text()
            os.killpg(process.pid, signal.SIGTERM); process.communicate(timeout=3)
        else:
            stdout, stderr = process.communicate(timeout=8)
            assert process.returncode == (1 if case == 'splash_stall' else 0), (case, stderr)
        if worker: worker.join(); assert not failure, failure
        assert started.exists() == (case not in ('unarmed', 'splash_stall'))
        assert not (mvp / 'game-started').exists()
        if case != 'unarmed':
            assert not (mvp / 'armed').exists() and not (lab / 'armed').exists()
        if case == 'normal':
            subprocess.run(['sh', str(ROOT / 'build/dispatch-platform-lab.sh')], env=env, check=True, timeout=2)
            assert not (mvp / 'game-started').exists(), 'Consumed marker restarted gameplay'
        checks.append('sparse PATH wrapper ' + case)
    return checks

