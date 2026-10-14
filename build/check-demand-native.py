"""Actual owned-output runner with an independently consuming native provider."""
from pathlib import Path
from hashlib import sha256
import json,struct,zlib,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-final-private-v2'
RT=ROOT/'build/demand-private-v1/runtime-v1'
def main():
 assert not (OUT/'native-proof.json').exists();native=OUT/'native';native.mkdir()
 core=OUT/'core/snes9x2005_plus_libretro.so';cb=core.read_bytes();rom=ROOT/'build/plus-a7-out/ff6.sfc';rb=rom.read_bytes()
 state=bytearray((ROOT/'build/ability-regression-private-v1/cases/001/scene.state').read_bytes())
 assert struct.unpack_from('<I',state,32)[0]==zlib.crc32(state[40:])&0xffffffff
 struct.pack_into('<II',state,20,zlib.crc32(cb)&0xffffffff,len(cb))
 name='game-%08x-%d-core-%08x-%d.state'%(zlib.crc32(rb)&0xffffffff,len(rb),zlib.crc32(cb)&0xffffffff,len(cb))
 (native/name).write_bytes(state)
 s=(ROOT/'build/snes-mvp/native-runner-check.c').read_text()
 s=s.replace('const char *trace_path="build/snes-mvp/out/native-runner-fault-fixture.txt";','char trace_path[1200];snprintf(trace_path,sizeof(trace_path),"%s/fault-fixture.txt",argv[3]);')
 s=s.replace('static uint64_t production_deadline;','''static uint64_t production_deadline;
static uint8_t output_slots[3][512*240+128] __attribute__((aligned(64)));
static unsigned output_slot,direct_calls;
void *board_video_target(size_t *bytes){*bytes=512*240+64;return output_slots[output_slot]+64;}''')
 s=s.replace('int board_video_reserve(void) { production_deadline=', 'int board_video_reserve(void) { output_slot=(output_slot+1)%3;production_deadline=')
 s=s.replace('    assert(data && w && h && pitch>=w*2);','''    assert(data && w && h && pitch>=w*2);
    if(data==output_slots[output_slot]+64){assert(w==256&&h<=239&&pitch==512);++direct_calls;}
    memset(output_slots[output_slot],0x93,sizeof(output_slots[output_slot])); /* completed source can be reused immediately */''')
 s=s.replace('    return 0;\n}', '    return 0;\n}')
 pos=s.rindex('    return 0;');s=s[:pos]+'    assert(direct_calls>=120);printf("PASS: %u real runner direct-output callbacks, slot reuse, native fault/retry, state loads and drain\\n",direct_calls);\n'+s[pos:]
 p=RT/'demand-native-check.c'
 if p.exists():assert p.read_text()==s, 'Preserve a qualified fixture; create a fresh version if its body changes.'
 else:p.write_text(s,newline='\n')
 libs=['-L'+str(ROOT/'build/sysroot/lib'),'-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
 exe=OUT/'native-check'
 subprocess.run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-D_TIME_BITS=32','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-I'+str(ROOT/'build/snes9x2005/libretro-common/include'),'/usr/arm-linux-gnueabihf/lib/crt1.o',str(p),str(ROOT/'build/glibc230-stat-compat.c'),*libs,'-o',str(exe)],cwd=ROOT,check=True)
 log=OUT/'native-check.log'
 with log.open('x') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(exe),str(rom),str(core),str(native)],cwd=ROOT,env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
 txt=log.read_text();assert 'real runner direct-output callbacks' in txt and 'two snapshot loads' in txt
 (OUT/'native-proof.json').write_text(json.dumps({'passed':True,'real_owned_runner_and_core':True,'physical_driver':False,'A7_performance_evidence':False,'log_sha256':sha256(log.read_bytes()).hexdigest(),'output':[l for l in txt.splitlines() if l.startswith('PASS:')]},indent=2)+'\n')
 print('\n'.join(l for l in txt.splitlines() if l.startswith('PASS:')))
if __name__=='__main__':main()
