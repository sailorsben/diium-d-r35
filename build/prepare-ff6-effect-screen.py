"""Prepare an owned, offline animation-substitution screen. No device writes."""
from pathlib import Path
from hashlib import sha256
import json, re, shutil, struct

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/ff6-effect-screen-private-v1'
assert not OUT.exists()
OUT.mkdir()
rom_path = ROOT / 'build/plus-a7-out/ff6.sfc'
rom = rom_path.read_bytes()
assert len(rom) == 3145728
assert sha256(rom).hexdigest() == '0f51b4fca41b7fd509e4b8f9d543151f68efa5e97b08493e4b2a0c06f5d8d5e2'
# The prior cause-map analysis owns the byte-matched ROM reconstruction proof.
prior = json.loads((ROOT / 'build/confuser-private-v1/analysis.json').read_text())
for path, expected in prior['source_and_capture_hashes'].items():
    assert sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
names = re.findall(r'^\s*(\w+)\s*;\s*(\d+)\s*$',
    (ROOT / 'build/ff6-disasm/src/data/attack_anim_prop.inc').read_text(), re.M)
props = (ROOT / 'build/ff6-disasm/src/data/attack_anim_prop.asm').read_text()
inits = (ROOT / 'build/ff6-disasm/src/btlgfx/anim_init.asm').read_text()
init_info = {}
for match in re.finditer(r'; \[ battle animation init \$([0-9a-f]+):\s*(.*?) \]', inits):
    start = match.end()
    end = inits.find('; [ battle animation init', start)
    body = inits[start:end if end >= 0 else len(inits)]
    address = re.search(r'@([0-9a-f]{4}):', body)
    if address:
        init_info[int(match[1], 16)] = {'description': match[2], 'pc': 0xc20000 + int(address[1], 16),
            'circle': 'InitCircle' in body, 'mode7': bool(re.search(r'mode.?7|Mode7', body)),
            'window_registers': sorted(set(re.findall(r'hW(?:12|34|OBJ)SEL', body))),
            'helper_calls': sorted(set(re.findall(r'\b(?:jsr|jmp)\s+(_c2[0-9a-f]+)', body)))}
entries = []
for name, number in names:
    index = int(number)
    assert index == len(entries)
    raw = rom[0x107fb2 + index * 14:0x107fb2 + (index + 1) * 14]
    assert len(raw) == 14
    body = re.search(r'^\s*attack_anim_prop ' + name + r'\s*\n(.*?)end_attack_anim_prop', props, re.M | re.S)
    assert body
    init_match = re.search(r'init_fn (\d+)', body[1])
    assert raw[10] == (int(init_match[1]) if init_match else 0), (index, name)
    init = raw[10] & 127
    pc = 0xc20000 + struct.unpack_from('<H', rom, 0x2e8d8 + init * 2)[0]
    entries.append({'index': index, 'name': name, 'init': init, 'init_pc': pc,
        'scripts': dict(re.findall(r'^\s*((?:sprite|bg1|bg3|extra)_(?:script|gfx))\s+(\w+)', body[1], re.M)),
        'init_source': init_info.get(init, {}), 'context': 'substituted animation in derived single-enemy Magitek cast'})
assert len(entries) == 406 and entries[134]['name'] == 'BIO_BLAST' and entries[136]['name'] == 'CONFUSER'
(OUT / 'catalog.json').write_text(json.dumps(entries, indent=2) + '\n')
core = OUT / 'core'
shutil.copytree(ROOT / 'build/confuser-private-v1/bg3-submask/core', core,
               ignore=shutil.ignore_patterns('.git', '*.o', '*.so'))
p = core / 'libretro.c'
s = p.read_text()
start = s.index('void d35_conf_pc(unsigned pc)')
end = s.index('\n', s.index('}', start))
s = s[:start] + '''static unsigned d35_screen_init_pc;
unsigned long long d35_screen[8];
__attribute__((visibility("default"))) void d35_screen_set(unsigned pc) {
 d35_screen_init_pc=pc;memset(d35_screen,0,sizeof(d35_screen));}
__attribute__((visibility("default"))) void d35_screen_read(unsigned long long *out) {
 for(unsigned i=0;i<8;i++){out[i]=d35_screen[i];d35_screen[i]=0;}}
void d35_conf_pc(unsigned pc) {
 if(pc==0xc2eede)++d35_conf[11];if(pc==0xc2ef0a)++d35_conf[12];
 if(pc==d35_screen_init_pc)++d35_screen[0];
 if(pc==0xc19cca && ICPU.Registers.Y.W==0 && ICPU.Registers.X.W==134*14)++d35_screen[1];
 if(pc==0xc2e8d0)++d35_screen[2];
}
''' + s[end:]
# These globals are declared by the source headers, after the original early hook.
s = s.replace('static unsigned d35_screen_init_pc;', '#include "source/snes9x.h"\n#include "source/cpuexec.h"\nstatic unsigned d35_screen_init_pc;')
p.write_text(s, newline='\n')
p = core / 'link.T'
p.write_text(p.read_text().replace('d35_conf_read;', 'd35_conf_read; d35_screen_set; d35_screen_read;'), newline='\n')
source = (ROOT / 'build/a7-pair-private-v1/equivalence.c').read_text()
source = source.replace('assert(argc==5 || argc==6 || argc==7);', 'assert(argc==8);')
source = source.replace('if(argc==7)', 'if(argc>=7)')
source = source.replace('rom=read_all(argv[3],&n); state=read_all(argv[4],&state_n);', '''rom=read_all(argv[3],&n); state=read_all(argv[4],&state_n);
    unsigned effect=0;const char *effect_digit=argv[7];assert(*effect_digit);
    while(*effect_digit) { assert(*effect_digit>='0' && *effect_digit<='9');effect=effect*10+(*effect_digit++-'0');assert(effect<406); }
    assert(n==3145728);
    unsigned init=rom[0x107fb2+effect*14+10]&127;
    unsigned init_pc=0xc20000u+rom[0x2e8d8+init*2]+(rom[0x2e8d9+init*2]<<8);
    /* Both cores get the same 14-byte in-memory animation-table overlay.
     * Mechanics/attacker/target remain the original Bio Blast controlled case. */
    memmove(rom+0x107fb2+134*14,rom+0x107fb2+effect*14,14);
    printf("CASE effect=%u init=%u init_pc=%06x overlay_bytes=14 context=single_enemy_magitek\\n",effect,init,init_pc);''')
source = source.replace('assert(profile_begin && profile_end);', '''assert(profile_begin && profile_end);
    void (*read_census)(unsigned long long *),(*read_hyp)(unsigned long long *),(*read_conf)(unsigned long long *),(*read_screen)(unsigned long long *);
    void (*set_screen)(unsigned);
    *(void **)(&read_census)=dlsym(candidate.handle,"d35_census_read");
    *(void **)(&read_hyp)=dlsym(candidate.handle,"d35_hyp_read");
    *(void **)(&read_conf)=dlsym(candidate.handle,"d35_conf_read");
    *(void **)(&read_screen)=dlsym(candidate.handle,"d35_screen_read");
    *(void **)(&set_screen)=dlsym(candidate.handle,"d35_screen_set");
    assert(read_census && read_hyp && read_conf && read_screen && set_screen);
    set_screen(init_pc);unsigned long long clear[128];read_census(clear);read_hyp(clear);read_conf(clear);
    unsigned long long seen_init=0,seen_table=0;
    puts("ROW columns=frame,renderer_entries,tile_calls,clipped_calls,neon_rows,depth_rejected_rows,tile_decodes,palette_builds,window_deferred,window_fallback,wrong_mode,color_window,window1,other_window2,half_add_rows,half_add_fast_rows,init_hits,table_hits,bg1_rows,bg2_rows,bg3_rows");''')
source = source.replace('if(!(f%30)) {', '''unsigned long long ce[128],hy[128],co[128],sc[8];
            read_census(ce);read_hyp(hy);read_conf(co);read_screen(sc);
            seen_init+=sc[0];seen_table+=sc[1];
            printf("ROW %u,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu\\n",
              f,co[0],hy[0],hy[1],ce[40],ce[43],ce[21],hy[7],co[2],co[3],co[4],co[7],co[8],co[9],co[96],co[102],sc[0],sc[1],co[24],co[25],co[26]);
            if(!(f%30)) {''')
source = source.replace('    assert(!split_frames);', '''    printf("IDENTITY init_hits=%llu table_hits=%llu\\n",seen_init,seen_table);
    assert(seen_init && seen_table);
    assert(!split_frames);''')
source = source.replace('complete Magitek Bio Blast scene replay', 'bounded animation-table substitution screen')
(OUT / 'screen.c').write_text(source, newline='\n')
(OUT / 'prepared.json').write_text(json.dumps({'rom_sha256': sha256(rom).hexdigest(),
    'state_sha256': sha256((ROOT / 'build/magitek-bio-private/scene.state').read_bytes()).hexdigest(),
    'source_reference_sha256': sha256((ROOT / 'build/plus-a7-out/plus-a7.so').read_bytes()).hexdigest(),
    'cases': len(entries), 'a7_timings': False, 'device_access': False,
    'coverage_limit': 'Animation substitution; ordinary command/target/monster/event mechanics are not qualified.'}, indent=2)+'\n')
print('Prepared 406 animation cases and offline counted current renderer')
