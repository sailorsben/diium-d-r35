"""Rebuild fresh research copies with compiler reports; never touch qualified cores."""
from pathlib import Path
from hashlib import sha256
import json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/compiler-research-private-v1'
FLAGS='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'
DUMPS='-fdump-tree-unswitch-details -fdump-ipa-inline-details -fdump-tree-optimized'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def prepare():
 assert not OUT.exists();OUT.mkdir()
 frozen={}
 for label,src in [('baseline',ROOT/'build/demand-visible-private-v3/core'),('combined',ROOT/'build/ppu-refinements-private-v5/combined')]:
  shutil.copytree(src,OUT/label,ignore=shutil.ignore_patterns('*.o','*.so'))
  for p in src.rglob('*'):
   if p.is_file() and p.suffix in ('.c','.h','.so'):frozen[p.relative_to(ROOT).as_posix()]=digest(p)
 (OUT/'frozen.json').write_text(json.dumps(frozen,indent=2)+'\n')
 print('Prepared fresh compiler-report copies; frozen qualified sources intact')
def build(label,extra='',object_only=False):
 target=OUT/label;assert target.exists() and not (target/'snes9x2005_plus_libretro.so').exists()
 # Fix the previously embedded library-version string; dump flags do not
 # intentionally alter optimized IR. Capture actual toolchain and invocations.
 args=['make','-B','-j3','platform=unix','USE_BLARGG_APU=1','LOAD_FROM_MEMORY=1','GIT_VERSION=" 7f3528e"',
  'CC=arm-linux-gnueabihf-gcc '+FLAGS+' '+DUMPS+' '+extra,
  'SHARED=-shared -nostdlib -flto=4 -O3 '+DUMPS+' '+extra+' -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T',
  'LDFLAGS=-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1']
 if object_only:args.insert(1,'source/apu_blargg.o')
 with (OUT/(label+'-build.log')).open('x') as f:subprocess.run(args,cwd=target,stdout=f,stderr=subprocess.STDOUT,check=True)
 for n,h in json.loads((OUT/'frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 print('Built research',label,digest(target/('source/apu_blargg.o' if object_only else 'snes9x2005_plus_libretro.so')),flush=True)
def clone(label,source):
 assert not (OUT/label).exists()
 src=ROOT/('build/demand-visible-private-v3/core' if source=='baseline' else 'build/ppu-refinements-private-v5/combined')
 shutil.copytree(src,OUT/label,ignore=shutil.ignore_patterns('*.o','*.so'))
def snapshot(label):
 p=OUT/label/'source/apu_blargg.c';s=p.read_text();a=s.index('static uint8_t* spc_run_until_( int32_t end_time )');b=s.index('/* Runs SPC to end_time',a)
 part=s[a:b];assert part.count('allow_time_overflow')==2
 part=part.replace('allow_time_overflow','call_allow_time_overflow').replace('{\n','{\n   const bool call_allow_time_overflow=allow_time_overflow;\n',1)
 p.write_text(s[:a]+part+s[b:],newline='\n')
def boundary(label):
 p=OUT/label/'Makefile';s=p.read_text();assert 'source/apu_blargg.o: CFLAGS' not in s
 p.write_text(s+'\nsource/apu_blargg.o: CFLAGS += -fno-lto\n',newline='\n')
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='clone':clone(sys.argv[2],sys.argv[3])
 elif sys.argv[1]=='snapshot':snapshot(sys.argv[2])
 elif sys.argv[1]=='boundary':boundary(sys.argv[2])
 elif sys.argv[1]=='object':build(sys.argv[2],object_only=True)
 else:build(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else '')
