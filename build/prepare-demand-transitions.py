"""Real-core synthetic resolution boundaries; no ROM modification or timings."""
from pathlib import Path
import shutil,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-final-private-v2'
HOOK='''
static unsigned d35_transition_kind,d35_transition_frame,d35_transition_fired;
static void d35_transition_start(void){if(d35_transition_kind==6)S9xSetPPU(0x35,0x2105);}
__attribute__((visibility("default"))) void d35_transition_set(unsigned kind,unsigned frame){
 S9xSetPPU(0,0x2133);S9xSetPPU(kind==6?0x35:0x31,0x2105);
 d35_transition_kind=kind;d35_transition_frame=frame;d35_transition_fired=0;
}
static void d35_transition_line(unsigned line){
 static const unsigned rows[8]={0,1,7,8,32,112,200,223};
 unsigned k=d35_transition_kind;
 if(!k||k==6||d35_transition_fired||line!=rows[d35_transition_frame%8])return;
 d35_transition_fired=1;
 if(k==1||k==3)S9xSetPPU(0x35,0x2105);
 if(k==2)S9xSetPPU(0x36,0x2105);
 if(k==3)S9xSetPPU(1,0x2133);
 if(k==4)S9xSetPPU(4,0x2133);
 if(k==5)S9xSetPPU(8,0x2133);
}
'''
def main():
 assert sys.argv[1:] in ([],['--deterministic']);deterministic=bool(sys.argv[1:]);prefix='transition-fixed' if deterministic else 'transition'
 for label,source in [(prefix+'-reference',ROOT/'build/common-band-private-v3/core'),(prefix+'-candidate',OUT/'core')]:
  target=OUT/label;assert not target.exists();shutil.copytree(source,target,ignore=shutil.ignore_patterns('*.o','*.so'))
  p=target/'source/gfx.c';s=p.read_text();anchor='void RenderLine(uint8_t C)\n{';assert s.count(anchor)==1
  s=s.replace(anchor,HOOK+'\n'+anchor+'\n   d35_transition_line(C);')
  if deterministic:
   s='static void d35_transition_start(void);\n'+s
   s=s.replace('void S9xStartScreenRefresh(void)\n{','void S9xStartScreenRefresh(void)\n{\n   d35_transition_start();')
   # Fixture-only deterministic initial host state in both cores. Never mask
   # emulated registers; retain every DMA transfer and CPU/APU instruction.
   d=target/'source/dma.c';t=d.read_text();a='      HDMAMemPointers [i] = NULL;';assert t.count(a)==1
   d.write_text(t.replace(a,'      HDMABasePointers[i]=NULL; /* common fixture reset; see reference-control.json */\n'+a),newline='\n')
  p.write_text(s,newline='\n')
  p=target/'link.T';p.write_text(p.read_text().replace('global:','global: d35_transition_set;'),newline='\n')
 s=(OUT/'compare.c').read_text();s=s.replace('assert(argc==8);','assert(argc==9);unsigned kind=lab_number(argv[8],10);assert(kind>=1&&kind<=7);')
 fields=40 if 'dc[40]' in s else 32;needle=f'    unsigned long long dc[{fields}];counts(dc);';assert s.count(needle)==1
 s=s.replace(needle,'''    void (*rt)(unsigned,unsigned),(*ct)(unsigned,unsigned);
    *(void **)(&rt)=dlsym(reference.handle,"d35_transition_set");*(void **)(&ct)=dlsym(candidate.handle,"d35_transition_set");assert(rt&&ct);
'''+needle)
 s=s.replace('        reference.pixels=reference.pcm=reference.videos=0;','''        if(kind==7&&frame&&!(frame%30)){active=&reference;assert(reference.unserialize(state+40,size));active=&candidate;assert(candidate.unserialize(state+40,size));}
        rt(kind,frame);ct(kind,frame);
        reference.pixels=reference.pcm=reference.videos=0;''')
 (OUT/(prefix+'-compare.c')).write_text(s,newline='\n')
 print('Prepared original/combined core clones with register-write seams, eight visible-line boundaries and state-load cycling')
if __name__=='__main__':main()
