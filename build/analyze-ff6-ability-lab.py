"""Verify owned lab receipts; package private checkpoints and publish no game bytes."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import csv, importlib.util, json, shutil, struct, sys, zlib

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-ability-lab-private-v1'

def digest(path):return sha256(path.read_bytes()).hexdigest()

def state_header(path):
    raw=path.read_bytes()
    assert raw[:8]==b'D35MVP01'
    version,rom_crc,rom_size,core_crc,core_size,size,crc,reserved=struct.unpack('<8I',raw[8:40])
    assert version==1 and not reserved and len(raw)==size+40 and zlib.crc32(raw[40:])==crc
    assert (rom_crc,rom_size,core_crc,core_size)==(0xa27f1c7a,3145728,0x5cb51346,798296)
    return f'game-{rom_crc:08x}-{rom_size}-core-{core_crc:08x}-{core_size}.state'

def analyze():
    ready=json.loads((OUT/'ready.json').read_text())
    assert digest(ROOT/'build/plus-a7-out/ff6.sfc')==ready['rom_sha256']
    assert digest(ROOT/'build/confuser-gameplay-private-v1/plus-a7.so')==ready['core_sha256']
    assert digest(OUT/'scene.state')==ready['base_sha256']
    receipts={}
    for path in OUT.rglob('check.json'):
        record=json.loads(path.read_text());folder=path.parent
        assert record['log_sha256']==digest(folder/'check.log')
        assert record['identities']['state']==digest(folder/'scene.state')==record['state_sha256']
        assert record['identities']['input']==digest(folder/'cast.txt')==record['input_sha256']
        assert record['identities']['check']==digest(OUT/'check')
        assert record['calls']==1200 and not record['a7_timing']
        text=(folder/'check.log').read_text()
        assert 'FAIL output' not in text and 'FAIL emulated state' not in text
        assert ('PASS 1200 calls:' in text)==(record['status']=='passed')
        assert record['returncode']==(0 if record['status']=='passed' else 4)
        receipts[folder.name]=record
    cases=[]
    main_manifest=next(p for p in (OUT/'cases-english.json',OUT/'cases-final.json',
        OUT/'cases-corrected.json',OUT/'cases.json') if p.exists())
    for manifest in (main_manifest,OUT/'skills-confirmed.json'):
        for case in json.loads(manifest.read_text()):
            folder=case.get('folder',f"select-{case['effect']:03d}")
            record=receipts[folder]
            assert all(record[k]==case[k] for k in ('effect','family','state_sha256','input_sha256'))
            cases.append(record)
    assert len(cases)==126 and sum(c['status']=='passed' for c in cases)==124
    assert len({c['effect'] for c in cases if c['status']=='passed'})==124
    identities=cases[0]['identities']
    for case in cases:
        for name in ('reference','candidate','check'):assert case['identities'][name]==identities[name]
    assert identities['reference']==digest(ROOT/'build/plus-a7-out/plus-a7.so')
    assert identities['candidate']==digest(ROOT/'build/ff6-effect-screen-private-v1/natural/core/snes9x2005_plus_libretro.so')
    selected={c.get('folder',f"select-{c['effect']:03d}") for c in cases}
    excluded=[r for name,r in receipts.items() if name not in selected]
    source_paths=[ROOT/'build'/name for name in ('prepare-ff6-ability-lab.py',
        'run-ff6-ability-lab.py','ff6-ability-lab-check.c','build-ff6-ability-lab.sh')]
    analysis={
        'version':'ff6-ability-lab-1','rom_modified':False,'rom_sha256':ready['rom_sha256'],
        'working_core_sha256':ready['core_sha256'], 'comparison_identities':identities,
        'card_access':False,'a7_performance_evidence':False,'production_gate_passed':False,
        'final_cases':len(cases),'requested_casts_passed':124,'needs_context':2,
        'exact_output_state_comparison_calls':126*1200,'calls_per_case':1200,
        'family_results':{family:dict(Counter(c['status'] for c in cases if c['family']==family))
            for family in sorted({c['family'] for c in cases})},
        'preserved_prior_receipts':len(excluded),'prior_receipt_results':dict(Counter(c['status'] for c in excluded)),
        'prior_attempts_counted_as_final_qualification':False,
        'resources':{'party_hp':9999,'party_mp':999,'enemy_hp':60000,'levels_and_attack_stats':'original'},
        'profiles':{'spellbook':['Magic','Lore','Magitek','Item'],
                    'skills':['Tools','SwdTech','Blitz','Dance'],'rage':['Rage','Magic','Lore','Item']},
        'unlocked':{'magic':54,'lore':24,'magitek':8,'tools':8,'blitz':8,'bushido':8,'dance':8,'rage_table_ids':255},
        'context_limits':[
            'Copied early Narshe single-enemy Magitek-party battle; this is an engineered test fixture.',
            '124 requested animation identities start and complete through normal commands in the original ROM.',
            'Soldier Rage sets monster ID 1 and Rage status, but the selected run chooses Fight; Fire is not qualified by that run.',
            'Water Rondo uses non-native terrain and ends without Dance status; El Nino is not qualified by that stumble.',
            'Native-terrain Wind Song starts/completes Wind Slash and compares exactly.',
            'Only Pummel and Dispatch are qualified among eight unlocked Blitzes/Bushidos; only one Dance outcome is qualified.',
            'Rage table IDs include unusual/boss entries, not a claim of 255 ordinary learnable or safe Rages.',
            'Enemy-only, item/weapon, event/field, reflected/multi-target and side/back contexts remain separate.',
            'QEMU verifies ARM execution and outputs; physical speed, audio reserve and repeated-cast stability remain unmeasured.'
        ],
        'rng_predictions':{'soldier_fire_first_choice_probability':0.5,
            'water_rondo_non_native_stumble_probability':0.5,
            'water_rondo_first_el_nino_probability':7/32,
            'native_wind_song_first_wind_slash_probability':7/16,
            'basis':'Original RandRage, RandDance/DanceRateTbl and ACTION_BATTLE_CMD::DANCE; unchanged RNG.'},
        'final_receipt_sha256':{(OUT/c.get('folder',f"select-{c['effect']:03d}")/'check.json').relative_to(ROOT).as_posix():
            digest(OUT/c.get('folder',f"select-{c['effect']:03d}")/'check.json') for c in cases},
        'source_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in source_paths},
    }
    package=OUT/'playable'
    checkpoints=[('spellbook',OUT/'ready-spellbook/scene.state'),
        ('skills',OUT/'ready-skills-complete/scene.state'),('rage',OUT/'ready-rage/scene.state')]
    checkpoints += [(f"summon-{c['effect']:03d}-{c['name'].lower()}",
        OUT/c.get('folder',f"select-{c['effect']:03d}")/'scene.state') for c in cases if c['family']=='esper']
    packaged=[]
    package.mkdir(exist_ok=True)
    for name,source in checkpoints:
        filename=state_header(source);target=package/name/'saves'/filename
        if target.exists():assert digest(target)==digest(source)
        else:target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        packaged.append({'name':name,'path':target.relative_to(ROOT).as_posix(),'sha256':digest(target)})
    analysis['private_playable_checkpoints']=packaged
    (OUT/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
    with (OUT/'coverage.csv').open('w',newline='') as stream:
        fields=['effect','name','family','status','calls','state_sha256','input_sha256','log_sha256']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        writer.writerows({k:c[k] for k in fields} for c in cases)
    lines=[]
    for case in cases:
        folder=OUT/case.get('folder',f"select-{case['effect']:03d}")
        lines.append(f"RECEIPT family={case['family']} effect={case['effect']} status={case['status']}")
        lines.extend(line for line in (folder/'check.log').read_text().splitlines()
            if line.startswith(('CASE ','IDENTITY ','PASS ','FAIL cast identity')))
    (OUT/'proof-summary.log').write_text('\n'.join(lines)+'\n')
    print(f'Verified {len(cases)} final cases,124 actual casts; preserved {len(excluded)} older receipts; packaged {len(packaged)} private checkpoints.')

def publish(names=('analysis.json','coverage.csv','proof-summary.log')):
    raw=(ROOT/'evidence/manifest.json').read_bytes();old=json.loads(raw)
    for entry in old['entries']:assert digest(ROOT/entry['published'])==entry['published_sha256']
    dest=ROOT/'evidence/2026-10-12/ability-lab'
    if names==('runner-proof.json',):
        assert dest.is_dir()
        proof=json.loads((OUT/'runner-proof.json').read_text())
        assert proof['calls']==360 and proof['snapshot_loads']==6 and not proof['physical_hardware']
        for result in proof['profiles']:
            assert result['two_loads_passed'] and not result['a7_timing']
            assert result['log_sha256']==digest(OUT/('runner-'+result['profile'])/'check.log')
    else:assert not dest.exists();dest.mkdir(parents=True)
    entries=[]
    for name in names:
        source=OUT/name;data=source.read_bytes();public=data.replace(b'\r\n',b'\n');target=dest/name
        assert not target.exists();target.write_bytes(public)
        entries.append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
            'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(public).hexdigest(),
            'bytes':len(public),'normalized':data!=public})
    spec=importlib.util.spec_from_file_location('lab_publisher',ROOT/'build/publish-snes-1.19.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    (ROOT/'evidence/manifest.json').write_bytes(module.append_manifest(raw,entries))
    assert json.loads((ROOT/'evidence/manifest.json').read_bytes())['entries'][:len(old['entries'])]==old['entries']
    print(f'Published {len(names)} bounded proofs; preserved all {len(old["entries"])} prior manifest entries.')

if __name__=='__main__':
    analyze()
    if len(sys.argv)==2 and sys.argv[1]=='publish':publish()
    elif len(sys.argv)==2 and sys.argv[1]=='publish-runner':publish(('runner-proof.json',))
