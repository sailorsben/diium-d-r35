"""Publish metadata and identified text only from the October 9 FAT recovery.

Never publish CHK allocation slack, card contents, SRAM or vendor binaries.
"""
from pathlib import Path
from hashlib import sha256
import importlib.util, json, statistics

ROOT = Path(__file__).resolve().parent.parent
RECOVERY = ROOT/'device-evidence/fat-recovery-20261009T152900Z'
STRICT = ROOT/'device-evidence/snes-mvp-return-20261009T153241Z'
PREFIX = 'evidence/2026-10-09/fat-recovery/'

def digest(p): return sha256(p.read_bytes()).hexdigest()
def load(name, filename):
    spec=importlib.util.spec_from_file_location(name, ROOT/'build'/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def publish():
    repair=json.loads((RECOVERY/'repair-result.json').read_text())
    assert repair['exit_code']==1 and repair['volume']['serial']=='11EB-1465'
    assert repair['prompts'][-1]['answer']=='Y' and 'Convert lost chains' in repair['prompts'][-1]['context']
    full=RECOVERY/'card-full-after-repair'
    archive=json.loads((full/'collection.json').read_text())
    assert archive['complete'] and archive['preexisting_readable_files_unchanged']==412
    assert len(archive['files'])==426 and not archive['missing'] and not archive['changed']
    for e in archive['files']: assert digest(full/'files'/e['path'])==e['sha256']
    # Exact post-restoration comparison: only the known empty SRAM changes.
    restoration=json.loads((RECOVERY/'sram-restoration.json').read_text())
    changed=[]
    for e in archive['files']:
        actual=digest(Path('D:/')/e['path'])
        if actual!=e['sha256']:
            changed.append(e['path'])
            assert e['path']==restoration['destination'] and actual==restoration['sha256']
    assert changed==[restoration['destination']]
    c=json.loads((STRICT/'collection.json').read_text())
    lab=json.loads((STRICT/'lab-collection.json').read_text())
    assert c['complete'] and not c['read_errors'] and not c['armed_present'] and not lab['lab_armed']
    for e in c['copied_and_hash_verified']: assert digest(STRICT/e['archive_path'])==e['sha256']
    for e in lab['copied']: assert digest(STRICT/'platform-lab'/e['relative_path'])==e['sha256']
    for path,h in c['production_hashes'].items(): assert digest(Path('D:/')/path)==h
    release=json.loads((ROOT/'releases/snes-mvp-1.18/manifest.json').read_text())
    for name,key in [('snes-mvp','binary_sha256'),('plus-a7.so','core_sha256'),('launch.sh','wrapper_sha256')]:
        assert digest(STRICT/'snes-mvp'/name)==release[key]
    assert digest(Path('D:/retro/showlogo'))=='436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b'
    def text(name):
        raw=(full/'files/FOUND.000'/name).read_bytes().split(b'\x00',1)[0]
        assert raw.endswith(b'\n') and all(b in (9,10,13) or 32<=b<127 for b in raw)
        return raw
    session=text('FILE0011.CHK');final_session=text('FILE0012.CHK');trace=text('FILE0009.CHK')
    assert trace==text('FILE0013.CHK')
    fields=dict(line.split('=',1) for line in session.decode().splitlines() if '=' in line)
    final_fields=dict(line.split('=',1) for line in final_session.decode().splitlines() if '=' in line)
    differences=[key for key in fields if fields[key]!=final_fields[key]]
    assert set(fields)==set(final_fields) and set(differences)=={'checkpoint_kernel_ns','session_elapsed_ns'}
    assert int(final_fields['checkpoint_kernel_ns'])>int(fields['checkpoint_kernel_ns'])
    assert fields['build_version']=='1.18' and fields['session_id']=='503-14018869000'
    assert fields['core_crc32']=='1047d56f' and fields['core_bytes']=='785704'
    assert fields['rom_crc32']=='a27f1c7a' and fields['rom_bytes']=='3145728'
    assert len(trace)==int(fields['pcm_error_detail'].split('trace_bytes=')[1])==27866
    assert b'child_pid=503\n' in trace and fields['pcm_error_detail'].startswith(trace.decode().splitlines()[2][8:])
    costs=[list(map(int,v.split(','))) for k,v in fields.items() if k.startswith('frame_cost_') and k!='frame_cost_columns']
    ordinary=[v for v in costs if v[0]!=int(fields['runs'])]
    assert len(ordinary)==23
    analyzer=load('pcm_recovery_analysis','analyze-pcm-flight.py')
    pcm=analyzer.analyze(RECOVERY/'recovered-text/FILE0009.CHK.txt',44100)
    result={'repair_exit':1,'final_read_only_health_exit':0,'volume_serial':'11EB-1465',
        'recovered_chains':14,'recovered_allocation_bytes':1472*1024,
        'post_repair_full_archive_files':426,'post_repair_full_archive_bytes':archive['bytes'],
        'preexisting_readable_files_unchanged_by_repair':412,
        'only_later_content_change':'Restore empty current FF6 SRAM to verified pre-test 8192-byte save',
        'newer_sram_identified':False,'all_recovered_originals_preserved_privately':True,
        'strict_mvp_files':len(c['copied_and_hash_verified']),'strict_lab_files':len(lab['copied']),
        'strict_collection_complete':True,'snapshots_stock_hook_and_1_18_payload_preserved':True,
        'game_and_lab_unarmed':True,'vesper_splash_installed':False,
        'recovered_session':{'id':fields['session_id'],'build':fields['build_version'],
            'runs':int(fields['runs']),'video_submitted':int(fields['video_submitted']),
            'held':int(fields['held']),'duplicates':int(fields['video_dupes']),
            'snapshot_load_successes':int(fields['snapshot_load_successes']),
            'active_calls_per_second':int(fields['runs'])/(int(fields['active_wall_ns'])/1e9),
            'ordinary_final_call_count':len(ordinary),
            'ordinary_final_mean_wall_ms':statistics.mean(v[3] for v in ordinary)/1e6,
            'ordinary_final_mean_main_cpu_ms':statistics.mean(v[4] for v in ordinary)/1e6,
            'error_detail':fields['pcm_error_detail'],
            'session_text_bytes':len(session),'pcm_text_bytes':len(trace),
            'two_finished_reports_differ_only_in':differences,
            'fatal_call_video_omission':'Final fatal audio callback prevents one last drawing; no intentional hold.'},
        'pcm':pcm,'limits':'Repair restores filesystem health, not an audio fix or physical card-health proof. Recovered PCM shows production deficit before pointer divergence; no controlled cache-speed comparison.'}
    (RECOVERY/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    selected={'analysis.json':(RECOVERY/'analysis.json').read_bytes(),
        'chkdsk-repair.txt':(RECOVERY/'chkdsk-repair.txt').read_bytes(),
        'chkdsk-final.txt':(RECOVERY/'chkdsk-final.txt').read_bytes(),
        'recovered-1.18-session.txt':session,'recovered-1.18-final-session.txt':final_session,
        'recovered-1.18-pcm.txt':trace}
    helper=load('recovery_publication','publish-snes-1.18.py')
    manifest=ROOT/'evidence/manifest.json';original=manifest.read_bytes()
    existing=json.loads(original)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in existing)
    for e in existing: assert digest(ROOT/e['published'])==e['published_sha256']
    additions=[]
    for name,raw in selected.items():
        output=raw.decode('utf-8-sig').replace('\r\n','\n').encode('utf-8')
        for bad in (b'GITHUB_TOKEN',b'Bearer ',b'github_pat_',b'ghp_',b'C:\\Users',b'.codex/attachments'):
            assert bad not in output
        target=ROOT/PREFIX/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(output)
        source_name={'recovered-1.18-session.txt':'recovered-text/FILE0011.CHK.txt',
            'recovered-1.18-final-session.txt':'recovered-text/FILE0012.CHK.txt',
            'recovered-1.18-pcm.txt':'recovered-text/FILE0009.CHK.txt'}.get(name,name)
        source=RECOVERY/source_name
        source_original=source.read_bytes()
        assert source_original.decode('utf-8-sig').replace('\r\n','\n').encode('utf-8')==output
        additions.append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
            'source_sha256':sha256(source_original).hexdigest(),'published_sha256':sha256(output).hexdigest(),
            'bytes':len(output),'normalized':source_original!=output})
    manifest.write_bytes(helper.append_manifest(original,additions))
    print(json.dumps(result,indent=2))

if __name__=='__main__': publish()
