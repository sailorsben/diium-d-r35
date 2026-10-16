"""Strict corrected-reference/candidate comparisons from inspected gameplay."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import csv,json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-fixes-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def build():
 s=(ROOT/'build/check-multigame.c').read_text();a=s.index('static unsigned scenario;');b=s.index('static void image(',a)
 s=s[:a]+'''extern int legacy_sscanf(const char *,const char *,...) __asm__("__isoc99_sscanf");
static uint16_t scripted[40000];
static int16_t controls(unsigned port,unsigned device,unsigned index,unsigned id){(void)index;if(port||device!=RETRO_DEVICE_JOYPAD)return 0;unsigned mask=scripted[frame];return id==RETRO_DEVICE_ID_JOYPAD_MASK?(int16_t)mask:id<16?(int)((mask>>id)&1):0;}
'''+s[b:]
 old="assert(argc==7);assert(argv[5][0]>='0' && argv[5][0]<='4' && !argv[5][1]);scenario=(unsigned)(argv[5][0]-'0');unsigned calls=6000;"
 assert s.count(old)==1
 s=s.replace(old,'''assert(argc==7||argc==8);unsigned calls=0,count,mask;char line[128];FILE *inputs=fopen(argv[5],"r");assert(inputs);while(fgets(line,sizeof(line),inputs)){assert(legacy_sscanf(line,"%u %x",&count,&mask)==2&&count&&mask<=65535&&calls+count<=40000);while(count--)scripted[calls++]=(uint16_t)mask;}assert(!fclose(inputs));''')
 anchor='/* Independent cold boots, as in the established equivalence oracle. */';assert s.count(anchor)==1
 s=s.replace(anchor,'''if(argc==8){size_t n;unsigned char *saved=read_all(argv[7],&n);assert(n==size);active=&ref;assert(ref.unserialize(saved,size));active=&test;assert(test.unserialize(saved,size));free(saved);}''')
 s=s.replace('unsigned char *target=allocation;','unsigned char *direct=allocation;void *scratch=NULL;assert(!posix_memalign(&scratch,64,512*240+256));memset(scratch,0xa5,512*240+256);unsigned char *target=direct;')
 s=s.replace('unsigned route=frame%3;','unsigned route=frame%3;target=route==1?scratch:direct;')
 s=s.replace('free(allocation);','free(allocation);free(scratch);')
 p=OUT/'gameplay-check.c';p.write_text(s,newline='\n')
 flags=['arm-linux-gnueabihf-gcc','-DUSE_BLARGG_APU','-std=gnu99','-O2','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-Ibuild','-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o',str(p),'-Lbuild/sysroot/lib','-Wl,--no-as-needed','-l:libdl-2.30.so','-l:libz.so.1','-l:libc-2.30.so','-l:libgcc_s.so.1','-o',str(OUT/'gameplay-check')]
 with (OUT/'gameplay-build.log').open('w') as f:subprocess.run(flags,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
 tag='-'+sys.argv[1] if len(sys.argv)>1 else '';assert tag in ('','-v2');result_path=OUT/('gameplay'+tag+'-result.json')
 assert not result_path.exists();build();fixture=json.loads((OUT/'gameplay-fixtures.json').read_text());core=OUT/'core/snes9x2005_plus_libretro.so';ref=OUT/'reference/snes9x2005_plus_libretro.so';q=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib']
 def game(case):
  i=case['game'];d=OUT/f'checked{tag}-{i}';d.mkdir();args=q+[str(OUT/'gameplay-check'),str(ref),str(core),str(ROOT/f'build/multigame-private-v3/game-{i}.sfc'),str(d/'frames.csv'),str(OUT/case['inputs']),str(d)]
  if case.get('state'):assert digest(OUT/case['state'])==case['state_sha256'];args+=[str(OUT/case['state'])]
  assert digest(OUT/case['inputs'])==case['inputs_sha256']
  with (d/'run.log').open('w') as f:r=subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  text=(d/'run.log').read_text();records=list(csv.DictReader((d/'frames.csv').open()));passed=r.returncode==0 and len(records)==case['calls'] and 'PASS calls=' in text
  print('GAMEPLAY',i,passed,r.returncode,text.splitlines()[-1:],flush=True)
  return {**case,'passed':passed,'returncode':r.returncode,'recorded_calls':len(records),'artifacts':{p.relative_to(OUT).as_posix():digest(p) for p in d.iterdir() if p.is_file()},'log_tail':text.splitlines()[-4:]}
 with ThreadPoolExecutor(max_workers=3) as pool:games=list(pool.map(game,fixture))
 result={'physical':False,'production_gate':False,'candidate_sha256':digest(core),'reference_sha256':digest(ref),'games':games,'source_sha256':digest(Path(__file__)),'generated_harness_sha256':digest(OUT/'gameplay-check.c'),'fixture_manifest_sha256':digest(OUT/'gameplay-fixtures.json')}
 result_path.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
