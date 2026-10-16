"""Isolate fixes from frozen physical candidate; never access the card."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-fixes-private-v1'
def apply_fixes(core):
 p=core/'source/dma.c';s=p.read_text(encoding='utf-8');old='               p->IndirectAddress += HDMAMemPointers [d] - HDMABasePointers [d];';assert s.count(old)==1
 s=s.replace(old,'''               /* IndirectAddress advances on each transfer below. Never add a
                * cached host-pointer difference at termination: a new frame
                * invalidates MemPointers while BasePointers may be stale. */''');p.write_text(s,encoding='utf-8',newline='\n')
 p=core/'source/apu_blargg.c';s=p.read_text(encoding='utf-8');anchor='void S9xAPUWritePort (int32_t port, uint8_t byte)';assert s.count(anchor)==1
 s=s.replace(anchor,'''/* Rendering Ranger's SYNC protocol races the instruction-granular SPC
 * acknowledgement. Complete the in-progress SPC instruction before publishing
 * the next CPU value, only for the identified compatibility case. */
static bool d35_complete_port_writes;
void S9xAPUSetPortWriteCompletion(bool enabled){d35_complete_port_writes=enabled;}
'''+anchor)
 old='   spc_run_until_( S9X_APU_GET_CLOCK(CPU.Cycles) ) [0x10 + port] = byte;';assert s.count(old)==1
 s=s.replace(old,'''   bool previous_overflow=allow_time_overflow;
   if(d35_complete_port_writes)allow_time_overflow=true;
   spc_run_until_( S9X_APU_GET_CLOCK(CPU.Cycles) ) [0x10 + port] = byte;
   allow_time_overflow=previous_overflow;''');p.write_text(s,encoding='utf-8',newline='\n')
 p=core/'source/apu_blargg.h';s=p.read_text(encoding='utf-8');anchor='void    S9xAPUAllowTimeOverflow(bool allow);';assert s.count(anchor)==1;p.write_text(s.replace(anchor,anchor+'\nvoid    S9xAPUSetPortWriteCompletion(bool enabled);'),encoding='utf-8',newline='\n')
 p=core/'source/memmap.c';s=p.read_text(encoding='utf-8');anchor='   /* APU timing hacks */';assert s.count(anchor)==1
 p.write_text(s.replace(anchor,anchor+'''\n#ifdef USE_BLARGG_APU
   /* Reset on every ROM load; all other games retain byte-identical APU timing. */
   S9xAPUSetPortWriteCompletion(match_id("AVCJ"));
#endif'''),encoding='utf-8',newline='\n')
 p=core/'source/a7_demand_output.h'
 if p.exists():
  s=p.read_text(encoding='utf-8');anchor='unsigned admit=d35_pending&&';assert s.count(anchor)==1
  p.write_text(s.replace(anchor,'/* SuperFX scenes fail compact-target equivalence; retain full layout. */\n unsigned admit=!Settings.SuperFX&&d35_pending&&'),encoding='utf-8',newline='\n')
def main():
 source=ROOT/'build/demand-visible-private-v3/core';assert not OUT.exists();OUT.mkdir()
 shutil.copytree(source,OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'))
 reference=ROOT/'build/common-band-private-v3/core';shutil.copytree(reference,OUT/'reference',ignore=shutil.ignore_patterns('*.o','*.so'))
 for core in (OUT/'core',OUT/'reference'):apply_fixes(core)
 (OUT/'preparation.json').write_text(json.dumps({'base_core_sha256':sha256((source/'snes9x2005_plus_libretro.so').read_bytes()).hexdigest(),'reference_sha256':sha256((reference/'snes9x2005_plus_libretro.so').read_bytes()).hexdigest(),'fixes':['HDMA termination host-pointer leak','Ranger AVCJ instruction-complete APU port writes'],'card_access':False},indent=2)+'\n')
if __name__=='__main__':main()
