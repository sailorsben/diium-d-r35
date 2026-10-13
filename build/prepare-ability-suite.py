"""Owned automated original-ROM ability fixtures; no card writes or core changes."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json, runpy, shutil, sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-suite-private-v1'
LAB=ROOT/'build/ff6-ability-lab-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):assert s.count(a)==1,a[:80];return s.replace(a,b)
def prepare(archive):
    archive=archive.resolve();a=json.loads((archive/'archive.json').read_text())
    assert a['fat_clean'] and a['card_writes']==0 and not OUT.exists()
    OUT.mkdir();(OUT/'cases').mkdir()
    core=ROOT/'build/confuser-gameplay-private-v1/plus-a7.so'
    assert digest(core)=='d5761eacc68fbcba91052de19d37ca9f159fb2b40df7c9272f49398b9b4f880a'
    shutil.copy2(core,OUT/'plus-a7.so')
    rom=(ROOT/'build/plus-a7-out/ff6.sfc').read_bytes()
    catalog=json.loads((ROOT/'build/ff6-effect-screen-private-v1/catalog.json').read_text())
    replay=runpy.run_path(str(ROOT/'build/prepare-ff6-ability-lab.py'))['replay']
    # Replay helper deliberately restricts ownership to its lab tree. A separate
    # owned derived subtree preserves every original profile and cast receipt.
    derived=LAB/'hardware-targets-v1';derived.mkdir()
    press=lambda mask:f'advance 8 {mask:x}\nadvance 30 0\n'
    specs=[]
    for c in json.loads((LAB/'cases-english.json').read_text()):
        specs.append((c['name'],c['family'],[c['effect']],
            LAB/c.get('folder',f"select-{c['effect']:03d}")/'scene.state','',
            (LAB/c.get('folder',f"select-{c['effect']:03d}")/'cast.txt').read_text()))
    for c in json.loads((LAB/'skills-confirmed.json').read_text()):
        if c['family']=='tools':specs.append((c['name'],'tools',[c['effect'],336] if c['effect']==331 else [c['effect']],LAB/c['folder']/'scene.state','',(LAB/c['folder']/'cast.txt').read_text()))
    buttons={'LEFT':0x40,'RIGHT':0x80,'DOWN':0x20,'UP':0x10,'DOWN_LEFT':0x60,
        'DOWN_RIGHT':0xa0,'UP_LEFT':0x50,'UP_RIGHT':0x90,'X_BUTTON':0x200,
        'Y_BUTTON':2,'R_BUTTON':0x800,'L_BUTTON':0x400}
    text=(ROOT/'build/ff6-disasm/src/data/blitz_code.asm').read_text()
    import re
    combos=re.findall(r'blitz_code (\w+)\s+(.*?)end_blitz_code',text,re.S)
    assert len(combos)==8
    for index,(name,body) in enumerate(combos):
        cast=''.join(f'8 {buttons[b]:x}\n12 0\n' for b in re.findall(r'blitz_btn (\w+)',body))+'8 100\n'
        specs.append((name,'blitz',[93+index],LAB/'select-extra-blitz-093/scene.state','',cast))
    for index in range(8):
        specs.append((catalog[85+index]['name'],'bushido',[85+index],
            LAB/'select-extra-bushido-085/scene.state',f'poke 7b82 {32*index+4:x}\n','8 100\n'))
    for index in range(8):
        ids=list(rom[0xffe80+index*4:0xffe84+index*4])
        steps=press(0x80)*(index%2)+press(0x20)*(index//2)
        specs.append((f'DANCE_{index}','dance',ids,LAB/'ready-dance-menu/scene.state',steps,'8 100\n20 0\n8 100\n'))
    for index in range(255):
        ids=list(rom[0xf4600+index*2:0xf4602+index*2])
        # Set remembered cursor, then open/redraw the real Rage list. The source
        # InitRageSelect reads row scroll and draws names from the actual list.
        row=index//2;scroll=max(0,row-3);visible=row-scroll
        steps=f'poke 892b {scroll:x}\npoke 892f {index%2:x}\npoke 8933 {visible:x}\n'+press(0x100)
        specs.append((f'RAGE_{index:03d}','rage',ids,LAB/'ready-rage/scene.state',steps,'8 100\n20 0\n8 100\n'))
    assert len(specs)==400
    def make(entry):
        seq,spec=entry;name,family,ids,base,steps,cast=spec
        patch={0x3a8f:0};conditions=['injured living allies','living high-HP enemy','MP headroom']
        def word(addr,value):patch[addr]=value&255;patch[addr+1]=value>>8
        for slot in range(3):
            for addr in (0x3bf4,0x2e78):word(addr+slot*2,5000)
            for addr in (0x3c08,0x2e88):word(addr+slot*2,500)
        word(0x3c08+8,999);word(0x3c30+8,999)
        # Selectors for level-based Lore get level60 (divisible by3,4,5).
        if any(i in ids for i in (148,149,150)):
            patch[0x3b18+8]=60;conditions.append('enemy level60 for level Lore')
        if any(i in ids for i in (48,49,80)):
            patch[0x3ee4+2]=0x88;word(0x3bf4+2,0);word(0x2e78+2,0)
            conditions.append('Wedge KO; caster alive')
            if ids in ([48],[49]):cast='8 100\n20 0\n8 20\n20 0\n8 100\n'
        if any(i in ids for i in (50,51,77)):
            patch[0x3ee4]=0x0d;conditions.append('caster poisoned/blind but able to act')
        if 44 in ids:
            patch[0x3ef8+8]=0x60;conditions.append('enemy has Safe/Shell for Dispel')
        if 151 in ids:
            patch[0x3ef8+8]=0x80;conditions.append('enemy has Reflect for Reflect Lore')
        commands=''.join(f'poke {addr:x} {value:x}\n' for addr,value in sorted(patch.items()))
        commands+=steps+'advance 1 0\nsave\nquit\n'
        state=replay(derived/f'{seq:03d}-{family}',base,commands)
        folder=OUT/'cases'/f'{seq:03d}';folder.mkdir();shutil.copy2(state,folder/'scene.state')
        (folder/'input.txt').write_text(cast,encoding='ascii')
        # Properties and low attack byte are frame-boundary identity evidence,
        # not an instruction-hook or a claim that all sub-frame events are seen.
        graphics=[i for i in ids if i<238 or family=='tools']
        expected=bytes([len(graphics)])
        for effect in graphics:
            local=effect-93 if family=='blitz' else effect-85 if family=='bushido' else effect-328 if family=='tools' else effect&255
            expected+=bytes([local])+rom[0x107fb2+effect*14:0x107fb2+(effect+1)*14]
        (folder/'expected.bin').write_bytes(expected)
        result={'seq':seq,'name':name,'family':family,'possible_attack_ids':ids,
            'conditions':conditions,'calls':1200,'state_sha256':digest(folder/'scene.state'),
            'input_sha256':digest(folder/'input.txt'),'expected_sha256':digest(folder/'expected.bin'),
            'random_or_conditional':family in ('rage','dance') or name=='RETORT'}
        (folder/'case.json').write_text(json.dumps(result,indent=2)+'\n')
        print('Fixture',seq,name,flush=True);return result
    with ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(make,enumerate(specs)))
    (OUT/'plan.json').write_text(json.dumps({'archive':archive.name,'version':'ability1',
        'working_core_sha256':digest(core),'cases':cases,'production_gate_passed':False,
        'renderer_changed':False,'authorization':'Stage on I, automated each ability; valid targeting; animation criterion.'},indent=2)+'\n')
    # Known pair runner already owns kernel clocks, live workers, deferred trace,
    # frequency inspection and truthful fatal PCM behavior. Change only replay.
    shutil.copytree(ROOT/'build/a7-pair-private-v1/runner',OUT/'runner',
        ignore=shutil.ignore_patterns('*.o','out','*-check.c','__pycache__'))
    shutil.copy2(ROOT/'build/plus-a7-profile.h',OUT/'plus-a7-profile.h')
    p=OUT/'runner/pair-host.h';s=p.read_text().replace('[500]','[1200]').replace('local>=500','local>=1200').replace('pair.csv','frames.csv').replace('1.19-pair1','1.19-ability1').replace('RAM_until_workers_join','RAM_until_audio_join_display_idle');p.write_text(s,newline='\n')
    shutil.copy2(ROOT/'build/ability-observer.h',OUT/'runner/ability-observer.h')
    p=OUT/'runner/runner.c';s=p.read_text();s=replace(s,'#include "pair-host.h"','#include "pair-host.h"\n#include "ability-observer.h"')
    s=replace(s,'save_ready=false;pair_begin();','save_ready=false;pair_begin();\n    if(!ability_bind(p_retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM),p_retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM))) { fail("Ability setup rejected");goto done; }')
    s=s.replace('limit>500','limit>1200')
    s=replace(s,'unsigned replay_frame=pair_start+(unsigned)s.runs;\n        s.buttons=(replay_frame<8 || (replay_frame>=28 && replay_frame<36))?1u<<RETRO_DEVICE_ID_JOYPAD_A:0;',
        's.buttons=ability_buttons((unsigned)s.runs);')
    s=replace(s,'p_retro_run();','p_retro_run();\n        ability_observe((unsigned)s.runs);')
    s=replace(s,'pcm_cost_flush(s.save_dir);pair_finish(s.save_dir,board_is_null(),s.failed);',
        'pcm_cost_flush(s.save_dir);pair_finish(s.save_dir,board_is_null(),s.failed);ability_finish(s.save_dir);')
    s=s.replace('1.19-pair1','1.19-ability1');p.write_text(s,newline='\n')
    s=p.read_text().replace('/* Both real worker owners have joined before any diagnostic SD flush. */',
        '/* Audio owner joined and display queue idle before diagnostic SD flush. */');p.write_text(s,newline='\n')
    wrapper=(ROOT/'build/a7-pair-private-v1/launch.sh').read_text().replace('snes-pair1','snes-ability1').replace('pair-suite','ability-suite').replace('1.19-pair1','1.19-ability1')
    (OUT/'launch.sh').write_text(wrapper,newline='\n')
    (OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /usr/retro/snes-ability1/launch.sh\n',newline='\n')
    shutil.copy2(archive/'retro/snes-pair1/ROM-PATH.txt',OUT/'ROM-PATH.txt')
    print('Prepared400 independent original-ROM cases on unchanged working core; no card writes')
if __name__=='__main__':prepare(Path(sys.argv[1]))
