"""Select real abilities in the isolated lab; preserve failures and completion proof."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import argparse, json, subprocess, runpy

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-ability-lab-private-v1'
Q=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib']
CAT=json.loads((ROOT/'build/ff6-effect-screen-private-v1/catalog.json').read_text())

def digest(p):return sha256(p.read_bytes()).hexdigest()
def press(mask):return f'advance 8 {mask:x}\nadvance 30 0\n'
def grid(index,columns=2):
    return press(0x80)*(index % columns)+press(0x20)*(index // columns)

def menus():
    assert not (OUT/'cases.json').exists()
    replay=runpy.run_path(str(ROOT/'build/prepare-ff6-ability-lab.py'))['replay']
    lore_menu=replay(OUT/'ready-lore-menu',OUT/'ready-spellbook/scene.state',
        press(0x20)+press(0x100)+'image\nsave\nquit\n')
    magitek_menu=replay(OUT/'ready-magitek-menu',OUT/'ready-spellbook/scene.state',
        press(0x20)*2+press(0x100)+'image\nsave\nquit\n')
    cases=[]
    def select(spec):
        effect,family,base,commands=spec
        folder=OUT/f'select-{effect:03d}'
        state=replay(folder,base,commands+'image\nsave\nquit\n')
        (folder/'cast.txt').write_text('8 100\n20 0\n8 100\n',encoding='ascii')
        case={'effect':effect,'name':CAT[effect]['name'],'family':family,
              'state_sha256':digest(state),'input_sha256':digest(folder/'cast.txt')}
        print('Selected',effect,case['name'],flush=True)
        return case
    specs=[(i,'magic',OUT/'ready-magic-menu/scene.state',grid(i) or 'advance 1 0\n') for i in range(54)]
    specs += [(139+i,'lore',lore_menu,grid(i,1) or 'advance 1 0\n') for i in range(24)]
    # Starting Magitek cursor remains Bio Blast (right column, second row).
    routes={131:[0x40,0x10],132:[0x10],133:[0x40],134:[],135:[0x40,0x20],136:[0x20],137:[0x40,0x20,0x20],138:[0x20,0x20]}
    specs += [(i,'magitek',magitek_menu,''.join(press(m) for m in steps) or 'advance 1 0\n') for i,steps in routes.items()]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(select,spec) for spec in specs]):cases.append(future.result())
    rom=(ROOT/'build/plus-a7-out/ff6.sfc').read_bytes()
    for effect in range(54,81):
        esper=effect-54;raw=rom[0x46ac0+effect*14:0x46ac0+(effect+1)*14]
        patch={0x208e:esper,0x208f:0x7f,0x2090:raw[0],0x2091:raw[5],
               0x161e:esper,0x3344:esper,0x3f2e:0}
        commands=''.join(f'poke {a:x} {v:x}\n' for a,v in patch.items())
        # Refresh the Magic window and use the normal summon menu transition.
        commands+=press(1)+press(0x100)+press(0x10)
        cases.append(select((effect,'esper',OUT/'ready-magic-menu/scene.state',commands)))
    (OUT/'cases.json').write_text(json.dumps(sorted(cases,key=lambda c:c['effect']),indent=2)+'\n')
    print('Prepared',len(cases),'normal-command cases; no animation substitutions',flush=True)

def qualify(selected):
    cases_path=next(p for p in (OUT/'skills-confirmed.json',OUT/'skills-final.json',OUT/'skills-cases.json') if p.exists()) if selected=='skills' else next(p for p in (OUT/'cases-english.json',OUT/'cases-final.json',OUT/'cases-corrected.json',OUT/'cases.json') if p.exists())
    cases=json.loads(cases_path.read_text())
    if selected not in ('all','skills'):
        requested=set(map(int,selected.split(',')));cases=[c for c in cases if c['effect'] in requested]
        assert len(cases)==len(requested)
    reference=ROOT/'build/plus-a7-out/plus-a7.so'
    candidate=ROOT/'build/ff6-effect-screen-private-v1/natural/core/snes9x2005_plus_libretro.so'
    def run(case):
        folder=OUT/case.get('folder',f"select-{case['effect']:03d}");log=folder/'check.log';receipt=folder/'check.json'
        identity={'state':digest(folder/'scene.state'),'input':digest(folder/'cast.txt'),
                  'reference':digest(reference),'candidate':digest(candidate),'check':digest(OUT/'check')}
        assert identity['state']==case['state_sha256'] and identity['input']==case['input_sha256']
        if receipt.exists():
            old=json.loads(receipt.read_text());assert old['identities']==identity and old['log_sha256']==digest(log)
            return old
        assert not log.exists(),f'Prior incomplete receipt retained: {log}'
        with log.open('x') as stream:
            result=subprocess.run(Q+['build/ff6-ability-lab-private-v1/check',
                str(reference.relative_to(ROOT)),str(candidate.relative_to(ROOT)),
                'build/plus-a7-out/ff6.sfc',str((folder/'scene.state').relative_to(ROOT)),
                str((folder/'cast.txt').relative_to(ROOT)),str(case['effect']),'1200'],
                cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
        text=log.read_text()
        status='passed' if result.returncode==0 else 'needs_context' if result.returncode==4 else 'failed'
        record={**case,'identities':identity,'returncode':result.returncode,'status':status,
                'log_sha256':digest(log),'calls':1200,'a7_timing':False}
        receipt.write_text(json.dumps(record,indent=2)+'\n')
        print(status.upper(),case['effect'],case['name'],flush=True)
        return record
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(run,case) for case in cases]):future.result()

def correct_lore():
    # Historical exploratory layout attempt. English LORE_SELECT actually sets
    # $39=0 (one column); see english_lore(). Preserve this rejected evidence.
    assert not (OUT/'cases-corrected.json').exists()
    cases=json.loads((OUT/'cases.json').read_text())
    replay=runpy.run_path(str(ROOT/'build/prepare-ff6-ability-lab.py'))['replay']
    for case in cases:
        if case['family']!='lore':continue
        folder=OUT/f"select-lore-fixed-{case['effect']:03d}"
        state=replay(folder,OUT/'ready-lore-menu/scene.state',
            (grid(case['effect']-139,2) or 'advance 1 0\n')+'image\nsave\nquit\n')
        (folder/'cast.txt').write_text('8 100\n20 0\n8 100\n',encoding='ascii')
        case.update(folder=folder.name,state_sha256=digest(state),input_sha256=digest(folder/'cast.txt'))
        print('Correct Lore layout',case['effect'],flush=True)
    (OUT/'cases-corrected.json').write_text(json.dumps(cases,indent=2)+'\n')

def correct_magic():
    assert not (OUT/'cases-final.json').exists()
    cases=json.loads((OUT/'cases-corrected.json').read_text())
    replay=runpy.run_path(str(ROOT/'build/prepare-ff6-ability-lab.py'))['replay']
    def select(case):
        effect=case['effect']
        # These first two original selections are already correct and preserved.
        if case['family']!='magic' or effect<2:return case
        folder=OUT/f'select-magic-fixed-{effect:03d}'
        state=replay(folder,OUT/'ready-magic-menu/scene.state',
            grid(effect,2)+'image\nsave\nquit\n')
        (folder/'cast.txt').write_text('8 100\n20 0\n8 100\n',encoding='ascii')
        case.update(folder=folder.name,state_sha256=digest(state),input_sha256=digest(folder/'cast.txt'))
        print('Correct Magic layout',effect,flush=True)
        return case
    corrected=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(select,c) for c in cases]):corrected.append(future.result())
    (OUT/'cases-final.json').write_text(json.dumps(sorted(corrected,key=lambda c:c['effect']),indent=2)+'\n')

def skills():
    assert not (OUT/'skills-cases.json').exists()
    replay=runpy.run_path(str(ROOT/'build/prepare-ff6-ability-lab.py'))['replay']
    rom=(ROOT/'build/plus-a7-out/ff6.sfc').read_bytes()
    patch={0x3cf8:54,0x3ba4:2,0x3a58:1}
    # Tools menu filters the *battle inventory*, not persistent inventory alone.
    for i in range(8):
        item=0xa3+i;target=rom[0x185000+item*30+14]
        for j,value in enumerate((item,0x40,target,1,255)):patch[0x2686+i*5+j]=value
    text=''.join(f'poke {a:x} {v:x}\n' for a,v in patch.items())+'advance 38 0\nimage\nsave\nquit\n'
    state=replay(OUT/'ready-skills-complete',OUT/'ready-skills/scene.state',text)
    tools=replay(OUT/'ready-tools-menu',state,press(0x100)+'image\nsave\nquit\n')
    rage=replay(OUT/'ready-rage-menu',OUT/'ready-rage/scene.state',press(0x100)+'image\nsave\nquit\n')
    # Representative real commands for each extra profile; RNG skills need their
    # actual resulting animation, never treating menu availability as completion.
    specs=[(125,'tools',tools,grid(1), '8 100\n20 0\n8 100\n'),
           (126,'tools',tools,grid(2), '8 100\n20 0\n8 100\n'),
           (93,'blitz',state,press(0x20)*2+press(0x100),
             '8 40\n12 0\n8 80\n12 0\n8 40\n12 0\n8 100\n'),
           (85,'bushido',state,press(0x20)+press(0x100), '8 100\n20 0\n8 100\n'),
           (0,'rage',rage,grid(1), '8 100\n20 0\n8 100\n')]
    cases=[]
    for effect,family,base,commands,cast in specs:
        folder=OUT/f'select-extra-{family}-{effect:03d}'
        selected=replay(folder,base,(commands or 'advance 1 0\n')+'image\nsave\nquit\n')
        (folder/'cast.txt').write_text(cast,encoding='ascii')
        cases.append({'effect':effect,'name':CAT[effect]['name'],'family':family,
            'folder':folder.name,'state_sha256':digest(selected),'input_sha256':digest(folder/'cast.txt')})
    (OUT/'skills-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    print('Prepared complete Tools inventory and five real skill-command checks',flush=True)

def dance():
    path=OUT/'skills-cases.json';cases=json.loads(path.read_text())
    assert not any(c['family']=='dance' for c in cases)
    replay=runpy.run_path(str(ROOT/'build/prepare-ff6-ability-lab.py'))['replay']
    menu=replay(OUT/'ready-dance-menu',OUT/'ready-skills-complete/scene.state',
                press(0x20)*3+press(0x100)+'image\nsave\nquit\n')
    folder=OUT/'select-extra-dance-111'
    state=replay(folder,menu,grid(5)+'image\nsave\nquit\n')
    (folder/'cast.txt').write_text('8 100\n',encoding='ascii')
    cases.append({'effect':111,'name':CAT[111]['name'],'family':'dance',
        'folder':folder.name,'state_sha256':digest(state),'input_sha256':digest(folder/'cast.txt'),
        'context':'Water Rondo is stochastic; only actual El Nino table/init/deinit hits qualify.'})
    path.write_text(json.dumps(cases,indent=2)+'\n')
    print('Prepared normal Water Rondo selection; El Nino must actually execute',flush=True)

def skill_contexts():
    assert not (OUT/'skills-final.json').exists()
    replay=runpy.run_path(str(ROOT/'build/prepare-ff6-ability-lab.py'))['replay']
    cases=json.loads((OUT/'skills-cases.json').read_text())
    final=[c for c in cases if c['family'] in ('blitz','bushido')]
    for old,new in ((125,329),(126,330)):
        source=next(c for c in cases if c['effect']==old)
        folder=OUT/f'select-tools-animation-{new}'
        folder.mkdir()
        import shutil
        shutil.copy2(OUT/source['folder']/'scene.state',folder/'scene.state')
        shutil.copy2(OUT/source['folder']/'cast.txt',folder/'cast.txt')
        final.append({**source,'effect':new,'name':CAT[new]['name'],'folder':folder.name,
            'context':'Tools uses AttackAnimProp NOISEBLASTER+tool index, separate from spell mechanics IDs.'})
    for family,profile,effect,steps in (
            ('rage','ready-rage',0,press(0x100)+grid(1)),
            ('dance','ready-skills-complete',111,press(0x20)*3+press(0x100)+grid(5)),
            ('dance-native','ready-skills-complete',101,press(0x20)*3+press(0x100))):
        folder=OUT/f'select-active-{family}-{effect:03d}'
        # Active is a normal game setting. This isolates Wait-mode pausing as a
        # possible confound; it does not guarantee the requested random outcome.
        state=replay(folder,OUT/profile/'scene.state',
            'poke 3a8f 0\n'+steps+'image\nsave\nquit\n')
        (folder/'cast.txt').write_text('8 100\n',encoding='ascii')
        final.append({'effect':effect,'name':CAT[effect]['name'],'family':family,
            'folder':folder.name,'state_sha256':digest(state),'input_sha256':digest(folder/'cast.txt'),
            'context':'Active battle mode; natural RNG and terrain rules retained.'})
    (OUT/'skills-final.json').write_text(json.dumps(final,indent=2)+'\n')
    print('Correct Tools graphics IDs; Active-mode Rage/Dance plus native-terrain control',flush=True)

def english_lore():
    """Use the conditional LANG_EN control flow, not the shared position table."""
    assert not (OUT/'cases-english.json').exists()
    replay=runpy.run_path(str(ROOT/'build/prepare-ff6-ability-lab.py'))['replay']
    cases=json.loads((OUT/'cases-final.json').read_text())
    for case in cases:
        if case['family']!='lore':continue
        folder=OUT/f"select-lore-english-{case['effect']:03d}"
        state=replay(folder,OUT/'ready-lore-menu/scene.state',
            (grid(case['effect']-139,1) or 'advance 1 0\n')+'image\nsave\nquit\n')
        (folder/'cast.txt').write_text('8 100\n20 0\n8 100\n',encoding='ascii')
        case.update(folder=folder.name,state_sha256=digest(state),input_sha256=digest(folder/'cast.txt'))
        print('English single-column Lore',case['effect'],flush=True)
    (OUT/'cases-english.json').write_text(json.dumps(cases,indent=2)+'\n')

def confirmed_skills():
    """Confirm the normal self-target step; retain every earlier attempt."""
    assert not (OUT/'skills-confirmed.json').exists()
    replay=runpy.run_path(str(ROOT/'build/prepare-ff6-ability-lab.py'))['replay']
    cases=json.loads((OUT/'skills-final.json').read_text())
    final=[c for c in cases if c['family'] in ('blitz','bushido')]
    for index in range(8):
        effect=328+index;folder=OUT/f'select-tools-complete-{effect:03d}'
        state=replay(folder,OUT/'ready-tools-menu/scene.state',
            (grid(index,2) or 'advance 1 0\n')+'image\nsave\nquit\n')
        (folder/'cast.txt').write_text('8 100\n20 0\n8 100\n',encoding='ascii')
        final.append({'effect':effect,'name':CAT[effect]['name'],'family':'tools',
            'folder':folder.name,'state_sha256':digest(state),'input_sha256':digest(folder/'cast.txt')})
    for case in cases:
        if case['family'] not in ('rage','dance','dance-native'):continue
        import shutil
        folder=OUT/('confirm-'+case['folder']);folder.mkdir()
        shutil.copy2(OUT/case['folder']/'scene.state',folder/'scene.state')
        (folder/'cast.txt').write_text('8 100\n20 0\n8 100\n',encoding='ascii')
        final.append({**case,'folder':folder.name,'input_sha256':digest(folder/'cast.txt')})
    (OUT/'skills-confirmed.json').write_text(json.dumps(final,indent=2)+'\n')
    print('Prepared all eight Tools and explicit Rage/Dance self-target confirmation',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['menus','qualify','correct-lore','correct-magic','skills','dance','skill-contexts','english-lore','confirmed-skills','qualify-skills'])
    parser.add_argument('--cases',default='all');args=parser.parse_args()
    if args.mode=='menus':menus()
    elif args.mode=='correct-lore':correct_lore()
    elif args.mode=='correct-magic':correct_magic()
    elif args.mode=='skills':skills()
    elif args.mode=='dance':dance()
    elif args.mode=='skill-contexts':skill_contexts()
    elif args.mode=='english-lore':english_lore()
    elif args.mode=='confirmed-skills':confirmed_skills()
    elif args.mode=='qualify-skills':qualify('skills')
    else:qualify(args.cases)
