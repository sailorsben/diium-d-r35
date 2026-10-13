"""Owned counter-free generalized renderer and 18 returned-context regressions."""
from pathlib import Path
from hashlib import sha256
import json, shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-regression-private-v1'
RETURN=ROOT/'device-evidence/a7-pair-before-20261013T063819Z'
SELECT=[14,19,20,23,40,57,67,73,110,111,149,150,177,231,233,58,84,86]
def digest(p):return sha256(p.read_bytes()).hexdigest()
def prepare():
    assert not OUT.exists();OUT.mkdir()
    origin=ROOT/'build/confuser-gameplay-private-v1/core'
    assert digest(origin/'snes9x2005_plus_libretro.so')=='d5761eacc68fbcba91052de19d37ca9f159fb2b40df7c9272f49398b9b4f880a'
    shutil.copytree(origin,OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so','.git'))
    (OUT/'core/source/a7_window.h').write_text((ROOT/'build/plus-a7-multi-window.h').read_text(),newline='\n')
    for p in (OUT/'core').rglob('*'):
        if p.suffix in ('.c','.h') and p.name!='a7_window.h':assert not any(x in p.read_text(errors='ignore') for x in ('d35_census','d35_hyp','d35_conf[')),p
    # The reusable window header declares counters only under this disabled flag.
    assert '#define D35_EFFECT_COUNTS' not in (OUT/'core/source/a7_window.h').read_text()
    shutil.copytree(ROOT/'build/ability-suite-private-v1/runner',OUT/'runner')
    for p in (ROOT/'build/ability-suite-private-v1').glob('*.h'):
        shutil.copy2(p,OUT/p.name)
    for p in (OUT/'runner').glob('*.[ch]'):
        p.write_text(p.read_text().replace('1.19-ability1','1.19-ability2'),newline='\n')
    old=json.loads((RETURN/'retro/snes-ability1/plan.json').read_text())['cases']
    plan={'version':'1.19-ability2','returned_archive':RETURN.name,'calls_per_case':1200,
          'production_gate_passed':False,'candidate_A7_saving_measured':False,
          'authorization':'Fix shared failure patterns and provide an automated subset of the largest set.',
          'cases':[]}
    for seq,index in enumerate(SELECT):
        original=RETURN/f'retro/snes-ability1/cases/{index:03d}'
        dest=OUT/f'cases/{seq:03d}';shutil.copytree(original,dest)
        c={**old[index],'seq':seq,'original_case':index}
        for name,key in [('scene.state','state_sha256'),('input.txt','input_sha256'),('expected.bin','expected_sha256')]:
            assert digest(original/name)==c[key]
        plan['cases'].append(c)
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    main=(ROOT/'build/ability-suite-main.c').read_text().replace('last=end?number(end):400','last=end?number(end):18').replace('last>400','last>18')
    (OUT/'main.c').write_text(main,newline='\n')
    wrapper=(ROOT/'build/ability-suite-private-v1/launch.sh').read_text().replace('snes-ability1','snes-ability2').replace('1.19-ability1','1.19-ability2')
    (OUT/'launch.sh').write_text(wrapper,newline='\n')
    (OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /usr/retro/snes-ability2/launch.sh\n',newline='\n')
    shutil.copy2(RETURN/'retro/snes-ability1/ROM-PATH.txt',OUT/'ROM-PATH.txt')
    # New checker can compare counter-free cores and collect counters on separate
    # inward-census cores. No emulated or host timing is used as A7 evidence.
    s=(ROOT/'build/ff6-ability-lab-check.c').read_text()
    s=s.replace('assert(set_screen && set_table && read_screen);set_screen(init_pc);set_table(effect);',
        'if(set_screen){set_screen(init_pc);}\n    if(set_table){set_table(effect);}')
    s=s.replace('    unsigned char *a=malloc(size)', '''    void (*census)(unsigned long long *),(*hyp)(unsigned long long *),(*conf)(unsigned long long *),(*flush)(unsigned long long *);
    *(void **)(&census)=dlsym(candidate.handle,"d35_census_read");
    *(void **)(&hyp)=dlsym(candidate.handle,"d35_hyp_read");
    *(void **)(&conf)=dlsym(candidate.handle,"d35_conf_read");
    *(void **)(&flush)=dlsym(candidate.handle,"d35_flush_read");
    unsigned long long clear[128];if(census)census(clear);if(hyp)hyp(clear);if(conf)conf(clear);if(flush)flush(clear);
    unsigned char *a=malloc(size)''')
    s=s.replace('unsigned long long sc[8];read_screen(sc);', 'unsigned long long sc[8]={0};if(read_screen)read_screen(sc);')
    s=s.replace('deinit_hits+=sc[3];', '''deinit_hits+=sc[3];
        if(census && hyp && conf && flush){
            unsigned long long ce[128],hy[128],co[128],fl[64];census(ce);hyp(hy);conf(co);flush(fl);
            printf("WORK %u,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu\\n",frame,co[0],hy[0],hy[1],ce[40],ce[21],hy[7],fl[0x26],fl[0x27],fl[0x32]);
        }''')
    s=s.replace('if(!init_hits || !table_hits || !deinit_hits)', 'if(set_table && (!init_hits || !table_hits || !deinit_hits))')
    s=s.replace('requested animation started/completed', 'bounded original-ROM replay; hook identity only when exported')
    (OUT/'compare.c').write_text(s,newline='\n')
    print('Prepared counter-free generalized Window2 core;18 fixtures including five Rages, eleven failures and controls')
if __name__=='__main__':prepare()
