"""Publish selected1.9 startup failure evidence; never export private progress."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json

ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261005T131939Z'
PREFIX='evidence/2026-10-05/snes-mvp-1.9-return/'
def digest(path): return sha256(path.read_bytes()).hexdigest()
def fields(path): return dict(line.split('=',1) for line in path.read_text().splitlines() if '=' in line)

def audit_progress(collected):
    previous=json.loads((ROOT/'device-evidence/snes-mvp-1.9-install-20261005T072714Z/protected.json').read_text())
    matched=[]
    for item in collected['copied_and_hash_verified']:
        name=item['card_path']
        if name in previous and ('/saves/' in name or '/states/' in name) and not name.endswith(('.txt','.txt.bak')):
            assert item['sha256']==previous[name],name
            matched.append(name)
    assert len(matched)==18
    return {'passed':True,'previously_protected_game_progress_files_unchanged':len(matched),
        'scope':'MVP SRAM, snapshots/import metadata and stock save slots present in the prior protection map',
        'excluded':'diagnostic text reports and their backups',
        'private_filenames_or_progress_published':False,'card_writes':0}

def publish():
    collected=json.loads((RETURN/'collection.json').read_text())
    assert not collected['armed_present'] and collected['card_writes']==0
    for item in collected['copied_and_hash_verified']:
        assert digest(RETURN/item['archive_path'])==item['sha256']
    lab=json.loads((RETURN/'lab-collection.json').read_text())
    assert not lab['lab_armed'] and len(lab['copied'])==49
    for item in lab['copied']: assert digest(RETURN/'platform-lab'/item['relative_path'])==item['sha256']
    release=json.loads((ROOT/'releases/snes-mvp-1.9/manifest.json').read_text())
    for name,key in (('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')):
        assert digest(RETURN/'snes-mvp'/name)==release[key]
    previous=json.loads((ROOT/'device-evidence/snes-mvp-1.9-install-20261005T072714Z/protected.json').read_text())
    progress_count=0
    for item in collected['copied_and_hash_verified']:
        name=item['card_path']
        if name in previous and name.endswith(('.srm','.state','.srm.bak','.state.bak')):
            assert item['sha256']==previous[name];progress_count+=1
    final=fields(RETURN/'snes-mvp/saves/last-session.txt')
    fresh=fields(RETURN/'snes-mvp/last-progress.txt')
    for report in (final,fresh):
        assert report['build_version']=='1.9' and report['mock_backend']=='0' and report['runs']=='0'
        assert report['core_crc32']==release['core_crc32'] and report['phase']=='finished'
        assert report['output_accepted_frames_including_priming']=='2823' and report['write_errors']=='1'
        assert report['sink_rate']=='44100' and report['pcm_period_frames']=='128' and report['pcm_buffer_frames']=='3712'
        assert report['error']=='Audio service startup failed: File descriptor in bad state'
    result={'version':'1.9','archive_verified':True,'one_shot_consumed':True,
        'copied_mvp_files':len(collected['copied_and_hash_verified']),'copied_lab_files':49,
        'previous_progress_files_unchanged':progress_count,'exact_released_payload':True,
        'emulation_runs':0,'accepted_rate':44100,'period_frames':128,'buffer_frames':3712,
        'accepted_priming_frames':2823,'successful_priming_frames':0,'startup_errno':77,
        'failure_seam':'priming transfer/status/START; exact operation not retained',
        'reported_state_boundary':'state2/queued0 is prewrite; failed after-write state unavailable',
        'source_defect':'1.9 issues START on queued frames without checking observed state',
        'vendor_autostart_cause':'not proven by retained device logs',
        'runtime_and_kernel_byte_tails':'empty; utility diagnosis not established',
        'speed_audio_stability':'no emulation performance or audible PCM qualification'}
    (RETURN/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    (RETURN/'progress-preservation.json').write_text(json.dumps(audit_progress(collected),indent=2)+'\n')
    spec=importlib.util.spec_from_file_location('historical_publisher',ROOT/'build/publish-snes-1.9.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    manifest_path=ROOT/'evidence/manifest.json';raw_manifest=manifest_path.read_bytes()
    manifest=json.loads(raw_manifest)
    assert not any(e['published'].startswith(PREFIX) for e in manifest['entries'])
    for e in manifest['entries']: assert digest(ROOT/e['published'])==e['published_sha256']
    selected={'analysis.json':RETURN/'analysis.json','progress-preservation.json':RETURN/'progress-preservation.json',
        'startup.log':RETURN/'snes-mvp/startup.log','progress.txt':RETURN/'snes-mvp/last-progress.txt',
        'session-final.txt':RETURN/'snes-mvp/saves/last-session.txt',
        'runtime-platform.txt':RETURN/'snes-mvp/runtime-platform.txt',
        'diagnostic-flush.log':RETURN/'snes-mvp/diagnostic-flush.log',
        'last-run.log':RETURN/'snes-mvp/last-run.log','kernel-tail.txt':RETURN/'snes-mvp/kernel-tail.txt'}
    additions=[]
    for name,source in selected.items():
        raw=source.read_bytes();output=raw.decode().replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
        target=ROOT/PREFIX/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(output)
        additions.append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
            'source_sha256':sha256(raw).hexdigest(),'published_sha256':sha256(output).hexdigest(),
            'bytes':len(output),'normalized':raw!=output})
    manifest_path.write_bytes(mod.append_manifest(raw_manifest,additions))
    print(json.dumps(result,indent=2))

if __name__=='__main__': publish()
