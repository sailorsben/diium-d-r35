"""Build/qualify passive UART observation plus the unchanged proven SPI reader."""
from pathlib import Path
from hashlib import sha256
import json,os,subprocess,uuid
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/uart-kernel-verify-private'
HOOK=b'# D35 one-shot read-only kernel UART verification, before stock SPI owner.\nif [ -f /usr/retro/uart-kernel-verify1/armed ]; then\n  /bin/sh /usr/retro/uart-kernel-verify1/launch.sh || exit 64\nfi\n'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rel(p):return p.resolve().relative_to(ROOT).as_posix()
def write(p,s):p.write_bytes(s.encode())
def run(args,want=0):
 p=subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,capture_output=True,timeout=60);assert p.returncode==want,(args,p.returncode,p.stdout.decode(errors='replace'),p.stderr.decode(errors='replace'));return p.stdout.decode()
def main():
 OUT.mkdir(exist_ok=True);checks=[];r=ROOT/'releases/spi-readback-1';m=json.loads((r/'manifest.json').read_text());assert m['software_checks_passed'] and not m['flash_writes'] and not m['global_config_writes']
 for n,h in m['source_hashes'].items():assert digest(ROOT/n)==h,n
 for n,h in m['release_hashes'].items():assert digest(r/n)==h,n
 (OUT/'spi-readback').write_bytes((r/'spi-readback').read_bytes());checks.append('Exact qualified/physically used fixed05,9f,03 two-pass reader retained')
 flags=['-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib']
 def compile(out,extra=[]):run(['arm-linux-gnueabihf-gcc',*flags,*extra,'/usr/arm-linux-gnueabihf/lib/crt1.o','build/uart-kernel-observe.c','-Lbuild/sysroot/lib','-Wl,--no-as-needed','-l:libc-2.30.so','-l:libgcc_s.so.1','-l:ld-2.30.so','-o',rel(out)])
 compile(OUT/'uart-observe');abi=run(['arm-linux-gnueabihf-readelf','-V',rel(OUT/'uart-observe')]);assert 'GLIBC_2.34' not in abi and 'GLIBC_2.4' in abi;(OUT/'abi.txt').write_text(abi);checks.append('ARM observer linked against firmware glibc2.30,32-bit time ABI')
 compile(OUT/'observer-fixture',['-DOBSERVE_NS=10000000ull']);root=OUT/'fixture-root';paths=['proc/interrupts','proc/tty/driver/gp serial','proc/stat','proc/modules','proc/version','proc/cmdline','proc/sys/kernel/random/boot_id']
 for n in paths:
  p=root/n;p.parent.mkdir(parents=True,exist_ok=True);write(p,'fixture '+n+'\n')
 inputs={n:digest(root/n) for n in paths};test=OUT/'observer-ok'
 assert not test.exists();run(['qemu-arm','-L','build/sysroot',rel(OUT/'observer-fixture'),rel(root),rel(test)])
 timing=dict(l.split('=',1) for l in (test/'timing.txt').read_text().splitlines());assert timing['failed']=='0' and int(timing['end_snapshot_start_ns'])-int(timing['begin_snapshot_end_ns'])>=10000000
 for i,n in enumerate(paths):assert (test/('before-'+['interrupts','serial','stat','modules','version','cmdline','boot-id'][i]+'.txt')).read_bytes()==(root/n).read_bytes()
 assert inputs=={n:digest(root/n) for n in paths};checks.append('Actual ARM observer copies exact passive snapshots and uses relative kernel-clock wait')
 run(['qemu-arm','-L','build/sysroot',rel(OUT/'observer-fixture'),rel(root),rel(test)],2);checks.append('Observer refuses existing result directory')
 (root/'proc/version').unlink();run(['qemu-arm','-L','build/sysroot',rel(OUT/'observer-fixture'),rel(root),rel(OUT/'observer-missing')],1);checks.append('Missing passive input is explicit failure, not a passing measurement')
 (OUT/'launch.sh').write_bytes((ROOT/'build/launch-uart-kernel-verify.sh').read_bytes());normal=(ROOT/'device-evidence/uart-kernel-firmware1/normal-init').read_bytes();assert digest(ROOT/'device-evidence/uart-kernel-firmware1/normal-init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
 (OUT/'init').write_bytes(b'#!/bin/sh\n'+HOOK+normal[len(b'#!/bin/sh\n'):]);shell=ROOT/'build/uart-fix-private/firmware-busybox';assert digest(shell)=='6f974778b29d96a7e825b04c526b0e2948ec4f8497ac5558cb5b4d713f058e2f'
 sh=['qemu-arm','-0','busybox','-L','build/sysroot',rel(shell),'sh'];run(sh+['-n',rel(OUT/'launch.sh')]);run(sh+['-n',rel(OUT/'init')]);checks.append('Exact firmware shell syntax for wrapper and original init plus one-shot hook')
 for label,obs,spi,want in [('normal',0,0,0),('observer-failure',1,0,64),('reader-failure',0,1,64),('after-failure',0,0,64)]:
  base=OUT/label;base.mkdir();events=base/'events';events.write_bytes(b'');(base/'armed').write_bytes(b'fixture\n')
  wrapper=(OUT/'launch.sh').read_text().replace('/usr/retro/uart-kernel-verify1',rel(base));write(base/'launch.sh',wrapper)
  write(base/'uart-observe','#!/bin/sh\nprintf "observer\\n" >> '+rel(events)+'\ncase "$2" in *uart-after) [ "$AFTER_FAIL" = 1 ] && exit 1 ;; esac\nexit "$OBS_EXIT"\n')
  write(base/'spi-readback','#!/bin/sh\nprintf "reader\\n" >> '+rel(events)+'\nexit "$SPI_EXIT"\n');run(['chmod','+x',rel(base/'uart-observe'),rel(base/'spi-readback')])
  run(['env','OBS_EXIT='+str(obs),'SPI_EXIT='+str(spi),'AFTER_FAIL='+str(int(label=='after-failure')),*sh,rel(base/'launch.sh')],want)
  assert not (base/'armed').exists() and (base/'consumed').read_bytes()==b'fixture\n'
  assert events.read_text().splitlines()==(['observer'] if obs else ['observer','reader'] if spi else ['observer','reader','observer'])
  old=events.read_bytes();run(sh+[rel(base/'launch.sh')]);assert events.read_bytes()==old;checks.append('Consume-first synchronous firmware wrapper, failure/replay guard: '+label)
 runid=uuid.uuid4().hex;installation={'version':'uart-kernel-verify1','run_id':runid,'expected_flash_sha256':'ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321','expected_kernel_sha256':'b1fe94004b84cbf8ee0ec3367466598bc9c8dd1cbfa9f55ae9373bbc6eefa459','passes':2,'flash_writes':False,'module_loads':False,'observer_window_ns':5000000000}
 (OUT/'installation.json').write_text(json.dumps(installation,indent=2)+'\n');(OUT/'armed').write_bytes((runid+'\n').encode())
 names=['spi-readback','uart-observe','launch.sh','installation.json'];q={'version':'uart-kernel-verify1','passed':True,'checks':checks,'reader_manifest_sha256':digest(r/'manifest.json'),'sources':{n:digest(ROOT/'build'/n) for n in ['uart-kernel-observe.c','launch-uart-kernel-verify.sh','prepare-uart-kernel-verify.py']},'payload_hashes':{n:digest(OUT/n) for n in names},'init_sha256':digest(OUT/'init'),'marker_sha256':digest(OUT/'armed'),'flash_writes':False,'physical_result':'PENDING'}
 (OUT/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks),'payload_hashes':q['payload_hashes']}))
if __name__=='__main__':main()
