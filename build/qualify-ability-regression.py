"""Exact replay, aligned work census, migrated identity and actual runner checks."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import csv,json,os,re,struct,subprocess,sys,zlib,statistics,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-regression-private-v1'
RETURN=ROOT/'device-evidence/a7-pair-before-20261013T063819Z'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(x for x in p.read_text().splitlines() if not x.startswith('#')))
def kv(p):return dict(x.split('=',1) for x in p.read_text().splitlines() if '=' in x)
def qualify():
    assert not (OUT/'qualification.json').exists()
    env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
    plan=json.loads((OUT/'plan.json').read_text());core=OUT/'plus-a7.so'
    reference=ROOT/'build/plus-a7-out/plus-a7.so';rom=ROOT/'build/plus-a7-out/ff6.sfc'
    assert digest(reference)=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
    failures={c['case']:c for c in json.loads((RETURN/'ability-analysis/failure-analysis.json').read_text())['failures']}
    (OUT/'exact').mkdir(exist_ok=True);(OUT/'census').mkdir(exist_ok=True)
    crc=zlib.crc32(core.read_bytes());migration=[]
    for c in plan['cases']:
        p=OUT/f"cases/{c['seq']:03d}/scene.state";raw=p.read_bytes()
        assert raw[:8]==b'D35MVP01' and len(raw)==40+struct.unpack_from('<I',raw,28)[0]
        assert zlib.crc32(raw[40:])==struct.unpack_from('<I',raw,32)[0]
        head=bytearray(raw[:40]);struct.pack_into('<II',head,20,crc,core.stat().st_size)
        p.write_bytes(head+raw[40:]);assert p.read_bytes()[40:]==raw[40:]
        migration.append({'case':c['seq'],'original_case':c['original_case'],'payload_sha256':sha256(raw[40:]).hexdigest(),'payload_unchanged':True})
        c['state_sha256']=digest(p)
        c['observed_effect_id']=failures[c['original_case']]['observed_effect_id'] if c['original_case'] in failures else c['possible_attack_ids'][0]
        (p.parent/'case.json').write_text(json.dumps(c,indent=2)+'\n')
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    def compare(job):
        c,label,candidate=job;folder=OUT/f"cases/{c['seq']:03d}";log=OUT/('exact' if label=='candidate' else 'census')/f"{c['seq']:03d}-{label}.log"
        if not log.exists():
            with log.open('x') as f:
                subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(reference),str(candidate),str(rom),str(folder/'scene.state'),str(folder/'input.txt'),str(c['observed_effect_id']),'1200'],env=env,check=True,stdout=f,stderr=subprocess.STDOUT,timeout=120)
        assert 'PASS 1200 calls' in log.read_text();print(c['seq'],c['name'],label,'exact',flush=True)
        return {'case':c['seq'],'original_case':c['original_case'],'label':label,'calls':1200,'passed':True,'core_sha256':digest(candidate),'log_sha256':digest(log)}
    jobs=[(c,'candidate',core) for c in plan['cases']]
    for c in plan['cases'][:11]:
        jobs.extend([(c,'current',ROOT/'build/ff6-effect-screen-private-v1/trace-current/core/snes9x2005_plus_libretro.so'),
                     (c,'general',ROOT/'build/ff6-effect-screen-private-v1/natural/core/snes9x2005_plus_libretro.so')])
    with ThreadPoolExecutor(max_workers=2) as pool:comparisons=list(pool.map(compare,jobs))
    fields=['renderer_entries','tile_calls','clipped_calls','neon_rows','tile_decodes','palette_builds','window1_left_flush','window1_right_flush','fixed_color_flush']
    census=[]
    for c in plan['cases'][:11]:
        def work(label):
            records=[list(map(int,l[5:].split(','))) for l in (OUT/f"census/{c['seq']:03d}-{label}.log").read_text().splitlines() if l.startswith('WORK ')]
            assert len(records)==1200 and [r[0] for r in records]==list(range(1200));return records
        old,new=work('current'),work('general');f=failures[c['original_case']]
        # The archived tail definition is the final16 ordinary calls before the
        # terminal publication call. Use archived frame numbers, not a new peak.
        frame_rows=rows(RETURN/f"retro/snes-ability1/run-{c['original_case']:03d}/frames.csv")
        tail=[int(x['frame']) for x in frame_rows[-17:-1]]
        assert len(tail)==16
        removed={key:statistics.mean(old[i][k+1]-new[i][k+1] for i in tail) for k,key in enumerate(fields)}
        before={key:statistics.mean(old[i][k+1] for i in tail) for k,key in enumerate(fields)}
        after={key:statistics.mean(new[i][k+1] for i in tail) for k,key in enumerate(fields)}
        census.append({'case':c['seq'],'original_case':c['original_case'],'effect':f['observed_effect_name'],'tail_frames':tail,
            'current':before,'general':after,'removed':removed,'A7_unit_prices_measured':False})
    # Exercise the actual new ELF, all migrated state headers, synthetic controls,
    # per-case teardown and logs. No QEMU duration is published as speed evidence.
    mock=OUT/'mock';mock.mkdir();shutil.copy2(core,mock/'plus-a7.so');shutil.copytree(OUT/'cases',mock/'cases')
    with (OUT/'mock.log').open('x') as stream:
        subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'ability-suite'),str(mock),str(rom)],env={**env,'D35_ABILITY_MOCK':'1','D35_MVP_NO_PACING':'1'},check=True,stdout=stream,stderr=subprocess.STDOUT,timeout=600)
    observed=[]
    for c in plan['cases']:
        d=mock/f"run-{c['seq']:03d}";s=kv(d/'last-session.txt');a=rows(d/'animation.csv');f=rows(d/'frames.csv')
        assert s['runs']==s['video_submitted']=='1200' and s['error']=='' and s['held']=='0'
        assert s['build_version']=='1.19-ability2' and s['core_crc32']==f'{crc:08x}'
        assert len(a)==len(f)==1200 and int(kv(d/'animation.csv')['#matching_property_samples'])>0
        assert s['audio_remaining_frames']=='0' and int(s['output_accepted_frames_including_priming'])==int(s['resampled_enqueued_frames'])+int(s['priming_silence_frames'])
        if c['family']=='rage':assert {int(x['rage_terra'],16) for x in a if x['rage_terra']!='ff'}=={c['original_case']-145}
        observed.append({'case':c['seq'],'original_case':c['original_case'],'calls':1200,'requested_properties_observed':True,'lossless_PCM_accounting':True})
    libs=['-L'+str(ROOT/'build/sysroot/lib'),'-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
    subprocess.run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-I'+str(ROOT/'build/snes9x2005/libretro-common/include'),'/usr/arm-linux-gnueabihf/lib/crt1.o',str(OUT/'runner/ability-native-check.c'),str(ROOT/'build/glibc230-stat-compat.c'),*libs,'-o',str(OUT/'native-check')],check=True)
    native=OUT/'native';native.mkdir();case=OUT/'cases/000'
    with (OUT/'native.log').open('x') as f:
        subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'native-check'),str(rom),str(core),str(case/'scene.state'),str(native)],env={**env,'D35_ABILITY_INPUT':str(case/'input.txt'),'D35_ABILITY_EXPECTED':str(case/'expected.bin')},check=True,stdout=f,stderr=subprocess.STDOUT,timeout=90)
    assert 'PASS: consuming native provider' in (OUT/'native.log').read_text()
    wrapper=(OUT/'launch.sh').read_text().replace('BASE=/usr/retro/snes-ability2','BASE=$D35_MVP_BASE').replace('TRIGGER=/usr/retro/snes-mvp','TRIGGER=$D35_MVP_BASE')
    (OUT/'fixture-launch.sh').write_text(wrapper,newline='\n')
    fixture=(ROOT/'build/ability-suite-private-v1/wrapper-check.py').read_text()
    (OUT/'wrapper-check.py').write_text(fixture,newline='\n')
    with (OUT/'wrapper.log').open('x') as f:
        subprocess.run([sys.executable,str(OUT/'wrapper-check.py'),str(OUT/'wrapper-fixtures')],env={**env,'D35_WRAPPER_UNDER_TEST':str(OUT/'fixture-launch.sh')},check=True,stdout=f,stderr=subprocess.STDOUT,timeout=120)
    assert 'zero diagnostic card writes or global sync during ready child' in (OUT/'wrapper.log').read_text()
    assert max(tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text()))<=(2,30)
    q={'version':'1.19-ability2','passed':True,'case_count':18,'calls_per_case':1200,'nominal_minutes':18*1200*16.6881545/60000,
        'core_sha256':digest(core),'core_crc32':f'{crc:08x}','core_bytes':core.stat().st_size,
        'runner_sha256':digest(OUT/'ability-suite'),'wrapper_sha256':digest(OUT/'launch.sh'),
        'production_gate_passed':False,'A7_saving_measured':False,'QEMU_timings_used':False,
        'native_client_qualified':True,'wrapper_qualified':True,'snapshot_identity_migrations':migration,
        'exact_comparisons':comparisons,'actual_runner_cases':observed,'aligned_tail_work_census':census,
        'limitations':['No physical candidate result; effect-specific savings are not priced.',
                       'Inward counters are offline only; physical suite has only existing coarse clocks and RAM observer.',
                       'Window generalization does not claim to reduce unchanged fixed-color or Mode7 paths.']}
    (OUT/'qualification.json').write_text(json.dumps(q,indent=2)+'\n')
    print('PASS:18 exact new-core replays;22 aligned census replays;18 actual-runner cases;native and wrapper seams')
if __name__=='__main__':qualify()
