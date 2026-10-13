"""Normal Magitek menu inputs, original ROM and actual ability mechanics."""
from pathlib import Path
import json, shutil, subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-effect-screen-private-v1'
dest=OUT/'natural';assert not dest.exists();dest.mkdir()
core=dest/'core'
shutil.copytree(OUT/'general/core',core,ignore=shutil.ignore_patterns('*.o','*.so','.git'))
p=core/'libretro.c';s=p.read_text()
s=s.replace('static unsigned d35_screen_init_pc;', 'static unsigned d35_screen_init_pc,d35_screen_table=134*14,d35_screen_started;')
s=s.replace('d35_screen_init_pc=pc;memset(d35_screen,0,sizeof(d35_screen));',
            'd35_screen_init_pc=pc;d35_screen_started=0;memset(d35_screen,0,sizeof(d35_screen));')
s=s.replace('if(pc==d35_screen_init_pc)++d35_screen[0];',
            'if(pc==d35_screen_init_pc){++d35_screen[0];d35_screen_started=1;}\n if(pc==0xc1b085 && d35_screen_started){++d35_screen[3];d35_screen_started=0;}')
s=s.replace('ICPU.Registers.X.W==134*14','ICPU.Registers.X.W==d35_screen_table')
s+='\n__attribute__((visibility("default"))) void d35_screen_table_set(unsigned index) {d35_screen_table=index*14;}\n'
p.write_text(s,newline='\n')
p=core/'link.T';p.write_text(p.read_text().replace('d35_screen_set;', 'd35_screen_set; d35_screen_table_set;'),newline='\n')
s=(OUT/'trace-screen.c').read_text()
s=s.replace('    memmove(rom+0x107fb2+134*14,rom+0x107fb2+effect*14,14);', '    /* Original ROM stays byte-for-byte unchanged for natural casts. */')
s=s.replace('overlay_bytes=14 context=single_enemy_magitek', 'overlay_bytes=0 context=normal_magitek_cast')
s=s.replace('set_screen(init_pc);unsigned long long clear[128];',
            'set_screen(init_pc);void (*set_table)(unsigned);*(void **)(&set_table)=dlsym(candidate.handle,"d35_screen_table_set");assert(set_table);set_table(effect);unsigned long long clear[128];')
s=s.replace('unsigned long long seen_init=0,seen_table=0;', 'unsigned long long seen_init=0,seen_table=0,seen_deinit=0;')
s=s.replace('seen_init+=sc[0];seen_table+=sc[1];', 'seen_init+=sc[0];seen_table+=sc[1];seen_deinit+=sc[3];')
s=s.replace('printf("IDENTITY init_hits=%llu table_hits=%llu\\n",seen_init,seen_table);',
            'printf("IDENTITY init_hits=%llu table_hits=%llu deinit_hits=%llu\\n",seen_init,seen_table,seen_deinit);')
s=s.replace('assert(seen_init && seen_table);', 'assert(seen_init && seen_table && seen_deinit);')
s=s.replace('complete Magitek Bio Blast scene replay', 'normal Magitek ability cast, original ROM, animation init/deinit verified')
(dest/'screen.c').write_text(s,newline='\n')
# Starting cursor is right column/Bio Blast. These are normal libretro inputs.
# Each direction is pressed8 calls, then released30 calls before the next step.
commands={131:[0x40,0x10],132:[0x10],133:[0x40],134:[],135:[0x40,0x20],136:[0x20],137:[0x40,0x20,0x20],138:[0x20,0x20]}
catalog=json.loads((OUT/'catalog.json').read_text())
Q=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib']
for index,steps in commands.items():
    folder=dest/f'select-{index}';folder.mkdir()
    text=''.join(f'advance 8 {mask:x}\nadvance 30 0\n' for mask in steps)+'image\nsave\nquit\n'
    # The no-movement control needs one released call to furnish an image.
    if not steps:text='advance 1 0\n'+text
    (folder/'inputs.txt').write_text(text)
    with (folder/'inputs.txt').open() as inputs,(folder/'replay.log').open('x') as log:
        subprocess.run(Q+['build/a7-pair-private-v1/replay',
            'build/confuser-gameplay-private-v1/plus-a7.so','build/plus-a7-out/ff6.sfc',
            'build/magitek-bio-private/scene.state','-',str(folder.relative_to(ROOT))],
            cwd=ROOT,stdin=inputs,stdout=log,stderr=subprocess.STDOUT,check=True)
    assert (folder/'scene.state').is_file()
(dest/'cases.json').write_text(json.dumps([{'index':i,'name':catalog[i]['name'],'directions':v} for i,v in commands.items()],indent=2)+'\n')
print('Prepared eight natural menu-selected abilities; original ROM, completion hook and separate private states')
