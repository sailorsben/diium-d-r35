"""Qualify the actual ARM lab and sparse-firmware boot seam; never claim speed."""
from pathlib import Path
from hashlib import sha256
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/platform-lab-out'
BIN = OUT / 'platform-lab'
SOURCES = ['build/platform-lab.c', 'build/platform-lab-kernels.h',
           'build/plus-a7-render.h', 'build/launch-platform-lab.sh',
           'build/dispatch-platform-lab.sh', 'build/build-platform-lab.sh',
           *['build/snes-mvp/' + n for n in
             ('board.c', 'board.h', 'timing.c', 'timing.h', 'startup.c',
              'startup.h', 'platform.c', 'platform.h', 'ui.c', 'ui.h')]]

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def records(p):
    return [dict(item.split('=', 1) for item in shlex.split(line) if '=' in item)
            for line in p.read_text().splitlines()]

def check():
    checked_binary = digest(BIN)
    source_hashes = {p: digest(ROOT / p) for p in SOURCES}
    qemu = ['qemu-arm', '-cpu', 'cortex-a7', '-L', str(ROOT / 'build/sysroot'),
            '-E', 'LD_LIBRARY_PATH=' + str(ROOT / 'build/sysroot/lib'), str(BIN)]
    result = subprocess.run(qemu + ['--selftest'], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert '12300' in result.stdout and 'byte-exact' in result.stdout
    (OUT / 'selftest.log').write_text(result.stdout + result.stderr)
    stamp = str(time.time_ns())
    smoke = OUT / ('smoke-' + stamp); smoke.mkdir()
    result = subprocess.run(qemu + ['--null', '--quick', '--supervise', '--output', str(smoke)],
                            capture_output=True, text=True, timeout=12)
    assert result.returncode == 0, result.stderr
    data = records(smoke / 'results.log')
    assert len([r for r in data if r['event'] == 'kernel']) == 9
    pipelines = [r for r in data if r['event'] == 'pipeline']
    assert len(pipelines) == 5
    assert all(int(r['frames']) > 0 for r in pipelines)
    assert all(r['submitted'] == r['scaled'] == r['flipped'] == '0' for r in pipelines), 'Null backend must not claim hardware work'
    assert any(r.get('status') == 'complete' for r in data if r['event'] == 'run_end')
    assert any(r['event'] == 'audio_skipped' for r in data)
    stall = OUT / ('stall-' + stamp); stall.mkdir()
    began = time.monotonic()
    result = subprocess.run(qemu + ['--null', '--fixture-stall', '--deadline-ms', '200',
                                    '--supervise', '--output', str(stall)],
                            capture_output=True, text=True, timeout=8)
    assert result.returncode == 72, result
    assert time.monotonic() - began < 4
    data = records(stall / 'results.log')
    assert [r['action'] for r in data if r['event'] == 'deadline'] == ['term', 'kill']
    assert data[-1]['event'] == 'supervisor_end' and data[-1]['killed'] == '1'
    versions = re.findall(r'GLIBC_(\d+)\.(\d+)', (OUT / 'abi.txt').read_text())
    assert versions and max((int(a), int(b)) for a, b in versions) <= (2, 30)
    asm = (OUT / 'disassembly.txt').read_text()
    assert 'vtbl.8' in asm and 'vld1.16' in asm, 'Expected emitted ARMv7 NEON kernels'
    wrapper_checks = check_wrapper(OUT / ('wrapper-' + stamp))
    assert checked_binary == digest(BIN)
    assert source_hashes == {p: digest(ROOT / p) for p in SOURCES}
    report = {'passed': True, 'hardware_qualified': False,
              'binary_sha256': checked_binary, 'source_hashes': source_hashes,
              'checks': ['12300 exact color/depth/flip/invalidation cases',
                         '4096-byte transport with arbitrary shorts/EAGAIN/EINTR',
                         'actual ARM null-backend five-phase supervisor smoke',
                         'actual stalled ARM child TERM/KILL and reap',
                         'GLIBC <= 2.30', 'emitted ARMv7 NEON lookup/load instructions',
                         *wrapper_checks]}
    (OUT / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

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
        (lab / 'launch.sh').write_bytes((ROOT / 'build/launch-platform-lab.sh').read_bytes())
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

if __name__ == '__main__':
    check()
