"""Fresh offline copies only; preserve shipped cores, earlier proofs and card."""
from pathlib import Path
import shutil, re, json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/confuser-private-v1'
OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'baseline').exists()
fields={0:'renderer_entries',1:'window_queries',2:'window_deferred',3:'window_fallback',
        4:'wrong_mode',5:'blank_or_hires',6:'mosaic',7:'color_window',8:'target_window1',9:'other_window2',
        10:'no_target',11:'confuser_init',12:'bio_init',13:'capture_valid',14:'capture_invalid',
        **{16+i:f'bg{i+1}_entries' for i in range(4)},
        **{24+i:f'bg{i+1}_rows' for i in range(4)},
        **{32+i:f'reg_{0x2100+i:04x}_writes' for i in range(64)}}
(OUT/'fields.json').write_text(json.dumps(fields,indent=2)+'\n')
for name in ('baseline','bg3-window'):
    dest=OUT/name
    shutil.copytree(ROOT/'build/bio-hypotheses-private/palette-fast-window-counts/core',dest/'core',
                    ignore=shutil.ignore_patterns('.git','*.o','*.so'))
    core=dest/'core'
    (core/'source/confuser.h').write_text('extern unsigned long long d35_conf[128];\nvoid d35_conf_pc(unsigned);\n')
    p=core/'libretro.c';s=p.read_text()
    s='''unsigned long long d35_conf[128];
__attribute__((visibility("default"))) void d35_conf_read(unsigned long long *out) {
 for(unsigned i=0;i<128;i++){out[i]=d35_conf[i];d35_conf[i]=0;}}
void d35_conf_pc(unsigned pc) { if(pc==0xc2eede)++d35_conf[11];if(pc==0xc2ef0a)++d35_conf[12]; }
'''+s
    p.write_text(s,newline='\n')
    p=core/'link.T';p.write_text(p.read_text().replace('d35_hyp_read;','d35_hyp_read; d35_conf_read;'),newline='\n')
    p=core/'source/cpuexec.c';s='#include "confuser.h"\n'+p.read_text()
    anchor='CPU.PCAtOpcodeStart = CPU.PC;';assert s.count(anchor)==4
    s=s.replace(anchor,anchor+'\n         d35_conf_pc(ICPU.ShiftedPB+(unsigned)(CPU.PC-CPU.PCBase));')
    p.write_text(s,newline='\n')
    p=core/'source/gfx.c';s='#include "confuser.h"\n'+p.read_text()
    s=s.replace('   ++d35_census[0];','   ++d35_census[0];++d35_conf[0];')
    s=s.replace('   d35_census[9+bg] += GFX.EndY-GFX.StartY+1;',
                '   ++d35_conf[16+bg];d35_conf[24+bg]+=GFX.EndY-GFX.StartY+1;\n   d35_census[9+bg] += GFX.EndY-GFX.StartY+1;')
    if name=='bg3-window':
        s=s.replace('bg==0 && d35_window_fetch(Y,','d35_window_fetch(bg,Y,')
        s=s.replace('(bg==0 && !d35_window_same(Y,Y+Lines))','(d35_window_is_target(bg) && !d35_window_same(Y,Y+Lines))')
    p.write_text(s,newline='\n')
    p=core/'source/ppu.c';s='#include "confuser.h"\n'+p.read_text()
    anchor='void S9xSetPPU(uint8_t Byte, uint16_t Address)\n{';assert s.count(anchor)==1
    s=s.replace(anchor,anchor+'\n   if(Address>=0x2100 && Address<0x2140)++d35_conf[32+Address-0x2100];')
    s=s.replace('if(!d35_window_defer()) { FLUSH_REDRAW(); }',
                'if(!d35_window_defer()) { ++d35_conf[3];FLUSH_REDRAW(); } else ++d35_conf[2];')
    p.write_text(s,newline='\n')
    p=core/'source/a7_window.h';s=p.read_text()
    if name=='bg3-window':
        s=s.replace('unsigned d35_window_fetch(unsigned,unsigned,struct d35_window_clip *);',
                    'unsigned d35_window_fetch(unsigned,unsigned,unsigned,struct d35_window_clip *);\nunsigned d35_window_is_target(unsigned);')
        s=s.replace('valid,left,right,inside,main_mask,sub_mask;','valid,left,right,inside,main_mask,sub_mask,target;')
        start=s.index('static unsigned d35_window_eligible(void)')
        end=s.index('void d35_window_reset',start)
        s=s[:start]+'''static unsigned d35_window_target(void) {
    return PPU.ClipWindow2Enable[0]?0:PPU.ClipWindow2Enable[2]?2:6;
}
unsigned d35_window_is_target(unsigned bg) { return bg==d35_window_target(); }
static unsigned d35_window_eligible(void)
{
    unsigned target=d35_window_target(),i;
    if(PPU.BGMode!=1) { ++d35_conf[4];return 0; }
    if(PPU.ForcedBlanking || (Memory.FillRAM[0x2133]&15u)) { ++d35_conf[5];return 0; }
    if(target>=3) { ++d35_conf[10];return 0; }
    if(PPU.BGMosaic[target] && PPU.Mosaic>1) { ++d35_conf[6];return 0; }
    if(Memory.FillRAM[0x2130]&0xf0u) { ++d35_conf[7];return 0; }
    if(PPU.ClipWindow1Enable[target]) { ++d35_conf[8];return 0; }
    /* BG4 has no renderer in Mode1; its enabled window cannot affect output. */
    for(i=0;i<6;i++) if(i!=target && i!=3 && PPU.ClipWindow2Enable[i]) { ++d35_conf[9];return 0; }
    return 1;
}
'''+s[end:]
        s=s.replace('r->inside=PPU.ClipWindow2Inside[0];','r->target=d35_window_target();r->inside=PPU.ClipWindow2Inside[r->target];')
        s=s.replace('Memory.FillRAM[0x212e]&1u','Memory.FillRAM[0x212e]&(1u<<r->target)')
        s=s.replace('Memory.FillRAM[0x212f]&1u','Memory.FillRAM[0x212f]&(1u<<r->target)')
        s=s.replace('unsigned d35_window_fetch(unsigned row,unsigned sub,struct d35_window_clip *clip)',
                    'unsigned d35_window_fetch(unsigned bg,unsigned row,unsigned sub,struct d35_window_clip *clip)')
        s=s.replace('!(r=&d35_window_rows[row])->valid','(!(r=&d35_window_rows[row])->valid || r->target!=bg)')
    else:
        start=s.index('static unsigned d35_window_eligible(void)');end=s.index('void d35_window_reset',start)
        s=s[:start]+'''static unsigned d35_window_eligible(void)
{
    unsigned i;
    if(PPU.BGMode!=1) { ++d35_conf[4];return 0; }
    if(PPU.ForcedBlanking || (Memory.FillRAM[0x2133]&15u)) { ++d35_conf[5];return 0; }
    if(PPU.BGMosaic[0] && PPU.Mosaic>1) { ++d35_conf[6];return 0; }
    if(Memory.FillRAM[0x2130]&0xf0u) { ++d35_conf[7];return 0; }
    if(PPU.ClipWindow1Enable[0]) { ++d35_conf[8];return 0; }
    if(!PPU.ClipWindow2Enable[0]) { ++d35_conf[10];return 0; }
    for(i=1;i<6;i++) if(PPU.ClipWindow2Enable[i]) { ++d35_conf[9];return 0; }
    return 1;
}
'''+s[end:]
    s='#include "confuser.h"\n'+s
    s=s.replace('    ++d35_hyp[80];','    ++d35_hyp[80];++d35_conf[1];')
    s=s.replace('d35_window_record_validity(row&255u,0);return;','++d35_conf[14];d35_window_record_validity(row&255u,0);return;')
    s=s.replace('    r->valid=1;','    ++d35_conf[13];r->valid=1;')
    p.write_text(s,newline='\n')
    replay=(ROOT/'build/bio-hypotheses-private/palette-fast-window-counts/replay.c').read_text()
    replay=replay.replace('    char path[1024],line[256];','''    void (*conf_read)(unsigned long long *);
    *(void **)(&conf_read)=dlsym(c.handle,"d35_conf_read");assert(conf_read);
    conf_read(unused);
    char path[1024],line[256];''')
    replay=replay.replace('                puts("");','''                puts("");
                unsigned long long conf[128];conf_read(conf);
                printf("CONF frame=%llu",(unsigned long long)total_frames);
                for(unsigned i=0;i<128;i++) { printf(" %llu",conf[i]); }
                puts("");''')
    (dest/'replay.c').write_text(replay,newline='\n')
    (dest/'capture').mkdir()
(OUT/'cast-input.txt').write_text('advance 8 100\nadvance 20 0\nadvance 8 100\nadvance 1164 0\nimage\nquit\n')
print('Prepared two offline Confuser hypotheses, retaining every earlier artifact')
