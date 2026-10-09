"""Publish curated survey/repair contracts only; all raw captures remain private."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,struct

ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261009T180632Z'
REPAIR=ROOT/'device-evidence/survey-return-20261009T180632Z'
INSTALL=ROOT/'device-evidence/snes-mvp-return-20261009T182253Z'
PREFIX='evidence/2026-10-09/device-survey-return/'

def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))

def power_key_contract():
    data=(RETURN/'device-survey/results/capture-0031.bin').read_bytes()
    h=sha256(data).hexdigest();assert h=='a754c50d9843eb94e163424988b86a313a642899441a7847aa3e60b393ac12eb'
    start=struct.unpack_from('<I',data,28)[0];size,count=struct.unpack_from('<HH',data,42)
    loads=[struct.unpack_from('<8I',data,start+i*size) for i in range(count)]
    def offset(a):
        for kind,off,virtual,_,length,_,_,_ in loads:
            if kind==1 and virtual<=a<virtual+length:return off+a-virtual
        raise ValueError(hex(a))
    assert struct.unpack_from('<I',data,offset(0x10664))[0]==0xebffff8d
    v=0x10660+8+struct.unpack_from('<I',data,offset(0x1068c))[0];o=offset(v)
    assert data[o:data.index(b'\x00',o)]==b'poweroff'
    return {'sha256':h,'call':'system(poweroff) at 0x10664, after GPIO operations',
        'limit':'Software shutdown request observed in code; actual flushing/unmount/power-removal order unverified.'}

def publish():
    a=read(REPAIR/'full-readable-card/collection.json')
    b=read(REPAIR/'full-card-after-repair/collection.json')
    assert a['complete'] and b['complete'] and not a['errors'] and not b['errors']
    old={e['path']:e for e in a['copied_and_hash_verified']}
    new={e['path']:e for e in b['copied_and_hash_verified']}
    assert len(old)==789 and len(new)==1310
    for name,e in old.items():assert e['sha256']==new[name]['sha256']
    for name,e in new.items():assert digest(REPAIR/'full-card-after-repair/files'/name)==e['sha256']
    spec=importlib.util.spec_from_file_location('survey_analysis',ROOT/'build/analyze-device-survey.py')
    analyzer=importlib.util.module_from_spec(spec);spec.loader.exec_module(analyzer)
    result=analyzer.analyze(RETURN/'device-survey');assert not result['complete']
    records=[json.loads(x) for x in (RETURN/'device-survey/results/report.jsonl').read_text().splitlines()]
    present={e['output'] for e in result['captured']}
    missing=[e for e in records if e.get('kind')=='capture' and e.get('output') and e['output'] not in present]
    nonempty=sum(e['bytes']>0 for e in missing)
    allocation=sum((e['bytes']+32767)//32768*32768 for e in missing)
    assert len(present)==329 and len(missing)==572 and nonempty==521 and allocation==17856*1024
    repair=read(REPAIR/'repair-result.json');assert repair['exit_code']==1
    assert repair['prompts'][-1]['answer']=='Y'
    qualification=read(ROOT/'releases/device-survey-2/qualification.json')
    assert qualification['software_checks_passed'] and len(qualification['checks'])==21
    summary={'physical_survey_complete':False,'report_ended':result['report_ended'],
        'wrapper_exit':result['wrapper_exit'],'marker_identity':result['identity'],
        'collector_totals':result['end'],'present_captures':329,'missing_captures':572,
        'missing_nonempty_captures':nonempty,'missing_empty_captures':51,
        'missing_capture_allocation_bytes':allocation,'recovered_chains':521,
        'repair_exit':1,'pre_repair_readable_files_unchanged':789,
        'post_repair_archived_files':1310,'stock_rom_deletion':'Before survey installation and clean FAT check',
        'shutdown_method':'Physical power switch/button, the device only shutdown control; no launcher shutdown option. Orderly filesystem shutdown is unverified.',
        'stock_shutdown_helper':power_key_contract(),
        'causal_limit':'New lost allocation matches survey output exactly; directory persistence is plausible, exact driver/media/shutdown cause unproved',
        'restore_ordering_correction':'Return restoration preceded health check; manager now refuses restoration writes on unhealthy FAT',
        'spi_declaration':{'path':'/soc/spi@C0090000/nor-flash@0','driver':'spidev','chip_select':0,'max_hz':20000000,'rx_bus_width':2},
        'usb':{'udc_directory_present':False,'gadget_config_directory_present':False,'enabled_dt_controller':'gp,gpa7xxxa-usbd at D1100000'},
        'survey_2':{'software_checks':21,'physical_execution':'pending','format':'One indexed CRC32 capture bundle and one report',
            **read(REPAIR/'survey-2-verification.json')},
        'limits':'No SPI transaction, chip ID, dump, physical flashing, recovery mechanism, internal splash replacement or audio fix qualified.'}
    source=REPAIR/'public-analysis.json';source.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
    selected={'analysis.json':source,'updater-contract.json':REPAIR/'updater-contract.json',
        'chkdsk-return.txt':RETURN/'chkdsk-return.txt','chkdsk-repair.txt':REPAIR/'chkdsk-repair.txt',
        'chkdsk-final.txt':REPAIR/'chkdsk-final.txt','chkdsk-postinstall-2.txt':REPAIR/'chkdsk-after-survey-2.txt',
        'installation-2.json':INSTALL/'survey-installation.json'}
    manifest=ROOT/'evidence/manifest.json';original=manifest.read_bytes();existing=json.loads(original)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in existing)
    for e in existing:assert digest(ROOT/e['published'])==e['published_sha256']
    additions=[]
    for name,p in selected.items():
        raw=p.read_bytes();normalized=raw.decode('utf-8-sig').replace('\r\r\n','\n').replace('\r\n','\n').replace('\r','\n').encode()
        for bad in [b'Bearer ',b'github_pat_',b'ghp_',b'C:\\Users',b'.codex/attachments']:assert bad not in normalized
        target=ROOT/(PREFIX+name);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(normalized)
        additions.append({'source':p.relative_to(ROOT).as_posix(),'published':PREFIX+name,
            'source_sha256':sha256(raw).hexdigest(),'published_sha256':digest(target),'bytes':len(normalized),'normalized':raw!=normalized})
    # Preserve every historical byte, including the manifest's original CRLF.
    closing=b'\r\n  ]\r\n}\r\n';assert original.endswith(closing)
    encoded=b',\r\n'.join(('\r\n'.join('    '+line for line in json.dumps(e,indent=2).splitlines())).encode() for e in additions)
    updated=original[:-len(closing)]+b',\r\n'+encoded+closing
    assert json.loads(updated)['entries']==existing+additions
    manifest.write_bytes(updated)
    print(json.dumps({'published_files':len(additions),'raw_captures_published':False,'private_files_verified':1310},indent=2))

if __name__=='__main__':publish()
