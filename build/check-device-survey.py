"""Qualify exact ARM collector, native bounds/failure seams, sparse shell wrapper.

Fixtures are independent files/device metadata. No physical device is touched.
"""
from pathlib import Path
from hashlib import sha256
import importlib.util, json, os, re, shutil, subprocess, tempfile, time
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/device-survey-out'
def linux(p):
    p=Path(p).resolve();return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def wsl(args,**kwargs):return subprocess.run(['wsl','--exec',*map(str,args)],check=True,**kwargs)
def mod(file):
    s=importlib.util.spec_from_file_location(file.replace('-','_').replace('.','_'),ROOT/'build'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def records(path):return [json.loads(x) for x in (path/'report.jsonl').read_text().splitlines()]
def files(root):
    result={}
    for p in root.rglob('*'):
        if p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400:continue
        if p.is_file():result[p.relative_to(root).as_posix()]=sha256(p.read_bytes()).hexdigest()
    return result
def run():
    wsl(['sh',linux(ROOT/'build/build-device-survey.sh')])
    wsl(['gcc','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-Wno-format-truncation',
         linux(ROOT/'build/device-survey.c'),'-o',linux(OUT/'native-survey')])
    checks=[]
    with tempfile.TemporaryDirectory(prefix='survey-check-',dir=OUT) as name:
        temp=Path(name);root=temp/'root';root.mkdir()
        fixture={
            'proc/cpuinfo':b'independent CPU fixture\n','proc/cmdline':b'rootfstype=ramfs\n',
            'proc/mtd':b'dev: size erasesize name\n','proc/partitions':b'254 17 123 card\n',
            'proc/slow.bin':b'delayed read\n','proc/limit.bin':b'z'*300,'proc/kcore':b'NEVER READ',
            'bin/nand_part_info':b'\x7fELF independent tool bytes','bin/nandsync':b'\x7fELF sync fixture',
            'sys/bus/spi/devices/spi0.0/modalias':b'spi:independent\n',
            'sys/bus/spi/devices/spi0.0/uevent':b'MODALIAS=spi:independent\n',
            'sys/firmware/devicetree/base/compatible':b'fixture,board\x00generalplus,gpa\x00',
            'system/lib/modules/common/spi-gp.ko':b'\x7fELF module fixture',
            'system/lib/modules/modules.order':b'common/spi-gp.ko\n',
            'proc/44/comm':b'showlogo\n','proc/44/status':b'State: S\n',
            'init.rc':b'/init.project.rc &\n','init.project.rc':b'/showlogo &\n',
        }
        for p,data in fixture.items():
            target=root/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        (root/'dev').mkdir();(root/'dev/fake-device').write_bytes(b'DEVICE MUST NOT BE OPENED')
        wsl(['ln','-s',linux(root/'proc/cpuinfo'),linux(root/'proc/symlink')])
        before=files(root)
        executables={'native':[linux(OUT/'native-survey')],
                     'arm':['qemu-arm','-cpu','cortex-a7','-L',linux(ROOT/'build/sysroot'),linux(OUT/'device-survey')]}
        for label,exe in executables.items():
            result=temp/label
            wsl(exe+[linux(root),linux(result),'30'])
            rs=records(result);assert rs[-1]['kind']=='complete' and not rs[-1]['capped'] and not rs[-1]['stuck_child']
            assert not rs[-1]['failures'],[r for r in rs if r.get('kind')=='capture' and r['errno'] not in [0,2,20]]
            captures={r['source']:r for r in rs if r['kind']=='capture' and not r['errno']}
            for source in ['/bin/nand_part_info','/bin/nandsync','/sys/bus/spi/devices/spi0.0/modalias',
                           '/sys/firmware/devicetree/base/compatible','/system/lib/modules/common/spi-gp.ko']:
                assert source in captures,(label,source,[r for r in rs if r.get('group') in ['device-tree','module-runtime-inventory']])
                assert (result/captures[source]['output']).read_bytes()==fixture[source[1:]],source
            assert '/proc/kcore' not in captures
            assert '/dev/fake-device' not in captures
            assert any(r['kind']=='metadata' and r['source']=='/dev/fake-device' for r in rs)
            checks.append(label+': exact tool/module/DT bytes; passive device metadata; missing interfaces retained')
            for path,wanted in [('/proc/limit.bin',0),('/proc/symlink',1),('/dev/fake-device',1),('/proc/kcore',1)]:
                result=temp/(label+'-'+str(len(checks)))
                wsl(exe+[linux(root),linux(result),'4',path,'64'])
                cap=next(r for r in records(result) if r['kind']=='capture')
                assert cap['errno']==wanted,(path,cap)
                if not wanted: assert cap['bytes']==64 and cap['truncated']
                checks.append(label+': bounded/denied '+path)
        # A real FIFO needs WSL's Linux filesystem (NTFS cannot represent it).
        linux_temp=subprocess.check_output(['wsl','--exec','mktemp','-d','/tmp/d35-survey-XXXXXX'],text=True).strip()
        try:
            wsl(['mkdir',linux_temp+'/proc']);wsl(['mkfifo',linux_temp+'/proc/fifo'])
            wsl([linux(OUT/'native-survey'),linux_temp,linux_temp+'/result','2','/proc/fifo','64'])
            rs=[json.loads(x) for x in subprocess.check_output(['wsl','--exec','cat',linux_temp+'/result/report.jsonl'],text=True).splitlines()]
            assert next(r for r in rs if r['kind']=='capture')['errno']==1
            checks.append('real FIFO rejected before open')
        finally:
            wsl(['python3','-c','import pathlib,shutil,sys; p=pathlib.Path(sys.argv[1]); assert p.parent==pathlib.Path("/tmp") and p.name.startswith("d35-survey-"); shutil.rmtree(p)',linux_temp])
        # Simulate a stalled read in an owned child, not the collector parent.
        shim=temp/'delay.c';shim.write_text(r'''
#define _GNU_SOURCE
#include <dlfcn.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <time.h>
ssize_t read(int fd,void *buf,size_t n) {
 static ssize_t (*real)(int,void *,size_t);
 if(!real) real=dlsym(RTLD_NEXT,"read");
 char path[64],dest[4096];snprintf(path,sizeof(path),"/proc/self/fd/%d",fd);
 ssize_t k=readlink(path,dest,sizeof(dest)-1);
 if(k>0) { dest[k]=0;if(strstr(dest,"/slow.bin")) { struct timespec t={5,0};syscall(SYS_nanosleep,&t,0); } }
 return real(fd,buf,n);
}
''',encoding='utf-8')
        wsl(['gcc','-shared','-fPIC',linux(shim),'-ldl','-o',linux(temp/'delay.so')])
        result=temp/'timeout';begin=time.monotonic()
        subprocess.run(['wsl','--cd',linux(temp),'--exec','env','LD_PRELOAD=./delay.so',linux(OUT/'native-survey'),
            linux(root),linux(result),'1','/proc/slow.bin','64'],check=True)
        assert time.monotonic()-begin<3
        assert next(r for r in records(result) if r['kind']=='capture')['errno']==110
        assert not records(result)[-1]['stuck_child']
        checks.append('stalled read: deadline, SIGKILL and owned child reap')
        # Sparse device shell: execute the exact archived BusyBox under QEMU.
        base=temp/'wrapper';base.mkdir();(base/'armed').write_bytes(b'fixture-run-id\n')
        launcher=base/'device-survey'
        launcher.write_text('#!/bin/sh\nmkdir "$2"\nprintf fixture > "$2/executed"\n',encoding='utf-8',newline='\n')
        wsl(['chmod','+x',linux(launcher)])
        busybox=ROOT/'device-evidence/snes-mvp-return-20261009T165057Z/vesper-boot-probe/results/busybox'
        tools=temp/'sparse-tools';tools.mkdir()
        for tool in ['mv','sync','mkdir']:wsl(['ln','-s','/bin/'+tool,linux(tools/tool)])
        env=['env','PATH='+linux(tools),'D35_SURVEY_BASE='+linux(base),'D35_SURVEY_ROOT='+linux(root)]
        call=env+['/usr/bin/qemu-arm','-cpu','cortex-a7','-L',linux(ROOT/'build/sysroot'),linux(busybox),'sh',linux(ROOT/'build/launch-device-survey.sh')]
        wsl(call);assert (base/'consumed').read_bytes()==b'fixture-run-id\n' and not (base/'armed').exists()
        assert (base/'results/executed').read_bytes()==b'fixture'
        baseline=files(base);wsl(call);assert baseline==files(base)
        checks.append('actual firmware BusyBox wrapper: consume first; next boot no-op')
        assert before==files(root),'Fixture source changed'
        manager=mod('manage-device-survey.py')
        original=b'#!/bin/sh\necho independent startup\n/usr/retro/main &\n'
        assert manager.patched_init(original).replace(manager.HOOK,b'',1)==original
        checks.append('hook removal restores independent init byte-for-byte')
        # Independent analyzer fixture: missing interfaces are expected;
        # truncation, failed wrapper durability and stale run identities aren't.
        analysis=mod('analyze-device-survey.py');a=temp/'analysis';(a/'results').mkdir(parents=True)
        (a/'consumed').write_text('run-a\n');(a/'installation.json').write_text(json.dumps({'run_id':'run-a'}))
        (a/'startup.log').write_text('survey_exit=0\n');(a/'results/capture-0001.bin').write_bytes(b'proof')
        rs=[{'kind':'capture','group':'identity','source':'/proc/cpuinfo','output':'capture-0001.bin','errno':0,'bytes':5,'truncated':False},
            {'kind':'capture','group':'identity','source':'/proc/mtd','output':None,'errno':2,'bytes':0,'truncated':False},
            {'kind':'complete','failures':0,'truncated':0,'capped':False,'stuck_child':False}]
        def emit(): (a/'results/report.jsonl').write_text('\n'.join(json.dumps(r) for r in rs)+'\n')
        emit();assert analysis.analyze(a)['complete']
        (a/'consumed').write_text('old-run\n');assert not analysis.analyze(a)['complete']
        (a/'consumed').write_text('run-a\n');rs[-1]['truncated']=1;emit();assert not analysis.analyze(a)['complete']
        rs[-1]['truncated']=0;rs[-1]['failures']=1;emit();assert not analysis.analyze(a)['complete']
        rs[-1]['failures']=0
        rs[-1]['truncated']=0;emit();(a/'startup.log').write_text('survey_exit=1\n');assert not analysis.analyze(a)['complete']
        checks.append('analyzer rejects stale identities, truncated census and failed wrapper; missing interfaces remain explicit')
    abi=(OUT/'abi.txt').read_text()
    versions=re.findall(r'Name: GLIBC_([0-9.]+)',abi)
    assert versions and all(tuple(map(int,v.split('.'))) <= (2,30) for v in versions),versions
    checks.append('exact ARM dependencies are GLIBC <= 2.30')
    (OUT/'qualification.json').write_text(json.dumps({'software_checks_passed':True,'checks':checks,
        'physical_execution':'pending'},indent=2)+'\n',encoding='utf-8',newline='\n')
    release=ROOT/'releases/device-survey-1';release.mkdir(exist_ok=True)
    for source,dest in [(OUT/'device-survey','device-survey'),(OUT/'abi.txt','abi.txt'),
                        (OUT/'qualification.json','qualification.json'),(ROOT/'build/launch-device-survey.sh','launch.sh')]:
        shutil.copyfile(source,release/dest)
    source_names=['build/device-survey.c','build/build-device-survey.sh','build/launch-device-survey.sh',
                  'build/check-device-survey.py','build/manage-device-survey.py','build/analyze-device-survey.py',
                  'build/review-device-survey.py','build/device-test-catalog.py']
    digest=lambda p:sha256(p.read_bytes()).hexdigest()
    manifest={'version':1,'software_checks_passed':True,'physical_execution':'pending',
        'source_hashes':{n:digest(ROOT/n) for n in source_names},
        'release_hashes':{n:digest(release/n) for n in ['device-survey','abi.txt','qualification.json','launch.sh']},
        'budget_seconds':30,'capture_bytes_limit':48*1024*1024,'file_bytes_limit':8*1024*1024,
        'jobs_limit':2500,'per_read_seconds':2,'raw_device_reads':False,'hardware_controls':False}
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'passed_checks':len(checks),'release':str(release),'physical_execution':'pending'},indent=2))
if __name__=='__main__':run()
