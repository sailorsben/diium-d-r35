"""Kill the real ARM runner before cleanup; retain fresh RAM progress and old report."""
from pathlib import Path
import os,subprocess,sys,time,zlib
root=Path(__file__).resolve().parents[2]
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
saves=out/'saves';saves.mkdir(exist_ok=True)
report=saves/'last-session.txt'
old=(root/'evidence/2026-10-04/snes-mvp-1.5/last-session.txt').read_bytes()
report.write_bytes(old)
progress=out/'progress.txt'
if progress.exists():progress.unlink()
env=dict(os.environ,D35_MVP_FRAMES='10000000',D35_MVP_PROGRESS_FILE=str(progress))
env.pop('D35_MVP_NO_PACING',None)
with (out/'runtime.log').open('wb') as log:
    proc=subprocess.Popen(['qemu-arm','-cpu','cortex-a7','-L',str(root/'build/sysroot'),
        '-E','LD_LIBRARY_PATH='+str(root/'build/sysroot/lib'),str(root/'build/snes-mvp/out/snes-mvp'),
        '--mock','--rom',str(root/'build/ff3.zip'),'--core',str(root/'build/plus-a7-out/plus-a7.so'),
        '--saves',str(saves)],env=env,stdout=log,stderr=log)
    try:
        deadline=time.monotonic()+10;fields={}
        while time.monotonic()<deadline:
            assert proc.poll() is None,'Runner exited before simulated abrupt shutdown'
            if progress.exists():
                fields=dict(line.split('=',1) for line in progress.read_text().splitlines() if '=' in line)
                if int(fields.get('runs','0'))>=30:break
            time.sleep(.03)
        assert int(fields.get('runs','0'))>=30,'No fresh running checkpoint'
        assert fields['build_version']=='1.9' and fields['core_crc32']==f'{zlib.crc32((root/"build/plus-a7-out/plus-a7.so").read_bytes())&0xffffffff:08x}'
        assert fields['session_id'] and fields['phase']=='running'
        assert fields['held']=='0' and int(fields['video_submitted'])==int(fields['runs'])
        assert int(fields['audio_worker_cpu_ns'])>0,'Live audio CPU unavailable'
        assert report.read_bytes()==old,'Old report was overwritten before final cleanup'
    finally:
        proc.kill();proc.wait(timeout=5)
assert report.read_bytes()==old and progress.read_text().find('session_id=')>=0
print('PASS: real ARM runner killed before cleanup retains fresh 1.9/core/session checkpoint and live worker CPU; old 1.5 report stays historical')
