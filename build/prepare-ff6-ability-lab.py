"""Build isolated playable FF6 ability snapshots; never writes ROM/card/progress."""
from pathlib import Path
from hashlib import sha256
import json, re, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/ff6-ability-lab-private-v1'
ROM = ROOT / 'build/plus-a7-out/ff6.sfc'
CORE = ROOT / 'build/confuser-gameplay-private-v1/plus-a7.so'
BASE = OUT / 'scene.state'  # One B press closed the prior Magitek submenu.
Q = ['qemu-arm', '-cpu', 'cortex-a7', '-L', 'build/sysroot', '-E',
     'LD_LIBRARY_PATH=build/sysroot/lib', 'build/a7-pair-private-v1/replay']

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def bootstrap():
    """Copy the private owned seed and close its Magitek submenu normally."""
    assert digest(ROM) == '0f51b4fca41b7fd509e4b8f9d543151f68efa5e97b08493e4b2a0c06f5d8d5e2'
    assert digest(CORE) == 'd5761eacc68fbcba91052de19d37ca9f159fb2b40df7c9272f49398b9b4f880a'
    seed=ROOT/'build/magitek-bio-private/scene.state'
    assert digest(seed) == 'bbcdf057f4bb26d51c5b46c5935887ed8bcd5d34a93bb87dce5391eb0120aa79'
    OUT.mkdir(exist_ok=True)
    assert not BASE.exists()
    state=replay(OUT/'bootstrap',seed,'advance 8 1\nadvance 30 0\nimage\nsave\nquit\n')
    shutil.copy2(state,BASE)

def replay(folder, state, commands):
    folder, state = Path(folder).resolve(), Path(state).resolve()
    assert folder.is_relative_to(OUT) and state.is_relative_to(ROOT) and state.is_file()
    folder.mkdir()
    (folder / 'input.txt').write_text(commands, encoding='ascii')
    with (folder / 'input.txt').open() as inputs, (folder / 'replay.log').open('x') as log:
        subprocess.run(Q + [str(CORE.relative_to(ROOT)), str(ROM.relative_to(ROOT)),
            str(state.relative_to(ROOT)), '-', str(folder.relative_to(ROOT))],
            cwd=ROOT, stdin=inputs, stdout=log, stderr=subprocess.STDOUT,
            check=True, timeout=120)
    return folder / 'scene.state'

def main():
    assert OUT.exists() and BASE.exists() and not (OUT / 'prepared.json').exists()
    assert digest(ROM) == '0f51b4fca41b7fd509e4b8f9d543151f68efa5e97b08493e4b2a0c06f5d8d5e2'
    assert digest(CORE) == 'd5761eacc68fbcba91052de19d37ca9f159fb2b40df7c9272f49398b9b4f880a'
    rom = ROM.read_bytes()
    dbg = (ROOT / 'build/ff6-disasm/build/en/rom/ff6-en.dbg').read_text(encoding='utf-8')
    # Check the byte-matched game's actual linker symbols, not cheat-site offsets.
    for name, address in {'wCmdList':0x7e202e, 'wSpellList':0x7e208e,
            'wRageList':0x7e257e, 'wDanceList':0x7e267e,
            'MagicProp':0xc46ac0, 'BattleCmdProp':0xcffe00,
            'wOwnedTools':0x7e3a9b, 'wNumKnownLores':0x7e3a87}.items():
        assert re.search(r'^sym\b[^\n]*name="'+name+r'"[^\n]*val=0x'+f'{address:X}'+r'\b',dbg,re.M), name
    profiles = {'spellbook':[2,12,29,1], 'skills':[9,7,10,19],
                'rage':[16,2,12,1]}
    facts = []
    for name, commands in profiles.items():
        patch = {}
        def byte(offset, value):
            assert 0 <= offset < 0x20000 and 0 <= value <= 255
            patch[offset] = value
        def word(offset, value):
            byte(offset,value & 255); byte(offset+1,value >> 8)
        # Primary Terra only; retain attacker level, magic/strength and normal mechanics.
        for i, command in enumerate(commands):
            for j, value in enumerate([command,0x7f,rom[0xffe00+command*2+1]]):
                byte(0x202e+i*3+j,value)
            byte(0x1616+i,command)
        for slot in range(3):
            for offset in (0x3bf4,0x3c1c): word(offset+slot*2,9999)
            for offset in (0x3c08,0x3c30): word(offset+slot*2,999)
        # Existing lone enemy gets a large legal 16-bit HP pool, not immortality.
        for offset in (0x3bf4,0x3c1c): word(offset+8,60000)
        # All magic and Lore menu records use the original ROM targeting/MP data.
        for spell in range(54):
            p=0x208e+4*(spell+1)
            raw=rom[0x46ac0+spell*14:0x46ac0+(spell+1)*14]
            for j,value in enumerate([spell,0x7f,raw[0],raw[5]]): byte(p+j,value)
            byte(0x3034+spell,spell);byte(0x3084+spell,spell+1)
            byte(0x1a6e+spell,255)
        for lore in range(24):
            attack=139+lore;p=0x208e+4*(55+lore)
            raw=rom[0x46ac0+attack*14:0x46ac0+(attack+1)*14]
            for j,value in enumerate([lore,0x7f,raw[0],raw[5]]): byte(p+j,value)
            byte(0x306a+lore,attack);byte(0x3084+attack,55+lore)
        # No equipped esper in base; separate named summons will be created later.
        for j,value in enumerate([255,255,255,0]): byte(0x208e+j,value)
        byte(0x3a87,24)
        for i in range(3): byte(0x1d29+i,255)
        for i in range(255): byte(0x257e+i,i)
        byte(0x257e+255,255);byte(0x3a9a,255)
        for i in range(32): byte(0x1d2c+i,255 if i<31 else 127)
        for i in range(8): byte(0x267e+i,i)
        byte(0x1d4c,255);byte(0x1d28,255);byte(0x1cf7,255)
        byte(0x2020,7);byte(0x3a80,8);byte(0x3a9b,255)
        # Tools checks the inventory IDs as well as the owned-tools bit mask.
        for i in range(8): byte(0x1869+i,0xa3+i);byte(0x1969+i,1)
        # Bushido's real command guard requires an eligible weapon flag.
        if name=='skills': byte(0x3ba4,0x02)
        commands_text=''.join(f'poke {a:x} {v:x}\n' for a,v in sorted(patch.items()))
        commands_text += 'advance 1 0\nadvance 8 100\nadvance 30 0\nadvance 8 1\nadvance 30 0\nimage\nsave\n'
        commands_text += 'peek 202e 12\npeek 208e 220\npeek 216a 96\npeek 3bf4 80\nquit\n'
        folder=OUT/name
        state=replay(folder,BASE,commands_text)
        (folder/'patches.json').write_text(json.dumps({'offsets':patch,
            'provenance':'Source-derived offline WRAM edits in a copied battle state; original ROM unchanged.'},indent=2)+'\n')
        facts.append({'profile':name,'commands':commands,'state_sha256':digest(state),
            'patch_bytes':len(patch),'magic':54,'lores':24,'rages':255,'dances':8,
            'blitzes':8,'bushidos':8,'tools':8})
        print('Prepared private playable profile',name,flush=True)
    # Open primary menu via ordinary input; later selections use only buttons.
    replay(OUT/'magic-menu',OUT/'spellbook/scene.state','advance 8 100\nadvance 30 0\nimage\nsave\nquit\n')
    (OUT/'prepared.json').write_text(json.dumps({'rom_sha256':digest(ROM),
        'core_sha256':digest(CORE),'base_sha256':digest(BASE),'profiles':facts,
        'rom_modified':False,'card_access':False,'a7_measurement':False,
        'coverage_limit':'Menu profiles are derived test states. Enemy-only, field and scripted contexts remain separate.'},indent=2)+'\n')
    print('Prepared full-list menu lab; no ROM/card writes',flush=True)

def finalize():
    """Refresh the game's owned menu/HP buffers; preserve the initial probe."""
    prepared=json.loads((OUT/'prepared.json').read_text())
    assert not (OUT/'ready.json').exists()
    facts=[]
    for name in ('spellbook','skills','rage'):
        patch={0x3a58:1}
        for slot in range(3):
            for base,value in ((0x2e78,9999),(0x2e80,9999),(0x2e88,999),(0x2e90,999)):
                offset=base+slot*2;patch[offset]=value & 255;patch[offset+1]=value >> 8
        if name=='skills':patch[0x3ba4]=2
        text=''.join(f'poke {a:x} {v:x}\n' for a,v in sorted(patch.items()))
        text+='advance 38 0\nimage\nsave\npeek 202e 12\npeek 3bf4 80\nquit\n'
        folder=OUT/f'ready-{name}'
        state=replay(folder,OUT/name/'scene.state',text)
        facts.append({'profile':name,'state_sha256':digest(state)})
    replay(OUT/'ready-magic-menu',OUT/'ready-spellbook/scene.state',
           'advance 8 100\nadvance 30 0\nimage\nsave\nquit\n')
    prepared['ready_profiles']=facts
    prepared['menu_refresh']='Source BTL_GFX_11 via w7e3a58; same HP/MP in mechanics and graphics buffers.'
    (OUT/'ready.json').write_text(json.dumps(prepared,indent=2)+'\n')
    print('Finalized three playable profiles with source-derived menu refresh',flush=True)

if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='bootstrap':bootstrap()
    elif len(sys.argv)==2 and sys.argv[1]=='finalize':finalize()
    else:main()
