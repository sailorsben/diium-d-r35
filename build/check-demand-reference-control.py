"""Confirm that the artificial 239-line schedule exposes a baseline HDMA bug."""
from pathlib import Path
import shutil,os,subprocess,json
from hashlib import sha256
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-final-private-v2'
def main():
 a=OUT/'transition-reference/snes9x2005_plus_libretro.so';b=OUT/'reference-control.so';assert not b.exists();shutil.copy2(a,b)
 s=(ROOT/'build/common-band-private-v3/ordinary-compare.c').read_text().replace('"plus-a7-equivalence.c"','"demand-equivalence.c"')
 s=s.replace('    unsigned char *a=malloc(size),*b=malloc(size);','''    void(*rt)(unsigned,unsigned),(*ct)(unsigned,unsigned);*(void **)(&rt)=dlsym(reference.handle,"d35_transition_set");*(void **)(&ct)=dlsym(candidate.handle,"d35_transition_set");assert(rt&&ct);
    printf("DMA_INDIRECT_OFFSET %zu STRIDE %zu FILLRAM_OFFSET %zu\\n",sizeof(SCPUState)+sizeof(SICPU)+sizeof(SPPU)+offsetof(SDMA,IndirectAddress),sizeof(SDMA),sizeof(SCPUState)+sizeof(SICPU)+sizeof(SPPU)+sizeof(SDMA)*8+0x10000+0x20000+0x20000);
    unsigned char *a=malloc(size),*b=malloc(size);''')
 s=s.replace('        reference.pixels=reference.pcm=reference.videos=0;', '        rt(4,frame);ct(4,frame);\n        reference.pixels=reference.pcm=reference.videos=0;')
 s=s.replace('return 3;}', 'unsigned d=0;for(unsigned k=0;k<size;k++)if(a[k]!=b[k]&&d++<40)printf("DIFF %u %02x %02x\\n",k,a[k],b[k]);return 3;}')
 p=OUT/'reference-control-compare.c';p.write_text(s,newline='\n')
 libs=['-L'+str(ROOT/'build/sysroot/lib'),'-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
 exe=OUT/'reference-control-compare'
 subprocess.run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-DUSE_BLARGG_APU','-D_TIME_BITS=32','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-no-pie','-nostdlib','-Ibuild','-I'+str(OUT),'-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o',str(p),*libs,'-o',str(exe)],cwd=ROOT,check=True)
 r=subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(exe),str(a),str(b),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/'build/ability-regression-private-v1/cases/001/scene.state'),str(ROOT/'build/ability-regression-private-v1/cases/001/input.txt'),'19','1200'],cwd=ROOT,env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},capture_output=True,text=True,timeout=180)
 (OUT/'reference-control.log').write_text(r.stdout+r.stderr)
 assert r.returncode==3 and 'FAIL emulated state frame=240' in r.stdout
 assert sha256(a.read_bytes()).hexdigest()==sha256(b.read_bytes()).hexdigest()
 data={'baseline_vs_identical_baseline_diverges':True,'same_binary_sha256':sha256(a.read_bytes()).hexdigest(),'failure_frame':240,'diagnostics':[l for l in r.stdout.splitlines() if l.startswith(('DMA_','DIFF','FAIL'))],'cause_source':'S9xStartHDMA resets HDMAMemPointers but retains stale HDMABasePointers. A zero-line termination subtracts NULL minus stale base and writes its host-derived low16 bits to IndirectAddress and $43x5/6.','final_core_changed_for_HDMA':False,'ignored_emulated_state_fields':False}
 (OUT/'reference-control.json').write_text(json.dumps(data,indent=2)+'\n');print('Confirmed identical baseline clones diverge at synthetic239 frame240 in HDMA IndirectAddress and mirror registers; no emulated fields masked')
if __name__=='__main__':main()
