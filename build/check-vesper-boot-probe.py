"""Exercise the actual passive shell capture with an independent proc fixture."""
from pathlib import Path
import os, subprocess, tempfile
ROOT=Path(__file__).resolve().parent.parent
def linux(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
with tempfile.TemporaryDirectory(prefix='boot-probe-',dir=ROOT/'build') as temp:
    base=Path(temp);proc=base/'proc';system=base/'root';out=base/'probe'
    (proc/'123').mkdir(parents=True);(proc/'1').mkdir();(proc/'self').mkdir()
    (system/'etc').mkdir(parents=True);out.mkdir()
    (out/'armed').write_bytes(b'one boot only\n')
    (system/'init.rc').write_bytes(b'/bin/showlogo &\n')
    (system/'etc/inittab').write_bytes(b'::sysinit:/init.rc\n')
    for name in ['comm','cmdline','maps','status']:
        (proc/'123'/name).write_bytes({'comm':b'showlogo\n','cmdline':b'/bin/showlogo\x00',
            'maps':b'00010000-00020000 r-xp /bin/showlogo\n','status':b'State: S\n'}[name])
    (proc/'123/exe').write_bytes(b'\x7fELF independent fixture bytes')
    (proc/'mounts').write_bytes(b'/dev/card /usr/retro vfat rw\n')
    (proc/'self/mountinfo').write_bytes(b'fixture root path\n')
    cmd=['wsl','--exec','env','D35_BOOT_PROBE_BASE='+linux(out),
         'D35_BOOT_PROBE_PROC='+linux(proc),'D35_BOOT_PROBE_ROOT='+linux(system),
         'D35_BOOT_PROBE_ROUNDS=1','sh',linux(ROOT/'build/probe-vesper-boot.sh')]
    subprocess.run(cmd,check=True)
    assert not (out/'armed').exists() and (out/'consumed').exists()
    assert (out/'results/showlogo-123.elf').read_bytes()==(proc/'123/exe').read_bytes()
    assert (out/'results/showlogo-123-cmdline').read_bytes()==b'/bin/showlogo\x00'
    assert (out/'results/init.rc').read_bytes()==(system/'init.rc').read_bytes()
    before={p.name:p.read_bytes() for p in (out/'results').iterdir()}
    subprocess.run(cmd,check=True)
    assert before=={p.name:p.read_bytes() for p in (out/'results').iterdir()}
    assert (proc/'123/exe').read_bytes()==b'\x7fELF independent fixture bytes'
print('PASS: actual shell captures owner/source bytes and consumed marker prevents a second run')
