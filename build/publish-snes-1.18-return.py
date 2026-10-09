"""Publish only verified safe return summaries; no private card/progress data."""
from pathlib import Path
from hashlib import sha256
import importlib.util, json, struct

ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261009T144358Z'
PREFIX='evidence/2026-10-09/snes-mvp-1.18-return/'
def digest(path):return sha256(path.read_bytes()).hexdigest()
def load(file):
    spec=importlib.util.spec_from_file_location('public_return',ROOT/'build'/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def publish():
    c=json.loads((RETURN/'collection.json').read_text(encoding='utf-8'))
    lab=json.loads((RETURN/'lab-collection.json').read_text(encoding='utf-8'))
    assert c['card_writes']==0 and not c['armed_present'] and not c['complete']
    assert len(c['copied_and_hash_verified'])==51 and len(c['read_errors'])==2
    for e in c['copied_and_hash_verified']:assert digest(RETURN/e['archive_path'])==e['sha256']
    assert not lab['lab_armed'] and len(lab['copied'])==49
    for e in lab['copied']:assert digest(RETURN/'platform-lab'/e['relative_path'])==e['sha256']
    release=json.loads((ROOT/'releases/snes-mvp-1.18/manifest.json').read_text())
    release_match={n:digest(RETURN/'snes-mvp'/n)==release[k] for n,k in
        (('snes-mvp','binary_sha256'),('plus-a7.so','core_sha256'),('launch.sh','wrapper_sha256'))}
    assert all(release_match.values())
    old=json.loads((ROOT/'device-evidence/snes-mvp-1.18-install-20261009T024539Z/protected.json').read_text())
    assert all(old[n]==h for n,h in c['production_hashes'].items())
    entries={e['card_path']:e for e in c['copied_and_hash_verified']}
    snapshots=[n for n in entries if '/saves/' in n or '/states/' in n]
    snapshots=[n for n in snapshots if n.endswith(('.state','.state.bak','.sv0','.sv1','.sv2','.sv3','.sv4'))]
    assert all(entries[n]['sha256']==old[n] for n in snapshots if n in old)
    new=[n for n in snapshots if n not in old]
    assert new==['retro/snes-mvp/saves/game-a27f1c7a-3145728-core-1047d56f-785704.state']
    original=bytearray((RETURN/'snes-mvp/saves/game-a27f1c7a-3145728-core-5ba71d2a-656816.state').read_bytes())
    struct.pack_into('<II',original,20,0x1047d56f,785704)
    assert (RETURN/entries[new[0]]['archive_path']).read_bytes()==original
    full=json.loads((RETURN/'card-full-before-repair/collection.json').read_text())
    assert full['card_writes']==0 and not full['complete'] and len(full['errors'])==2
    for e in full['copied_and_hash_verified']:assert digest(RETURN/'card-full-before-repair/files'/e['path'])==e['sha256']
    zero=[e['card_path'] for e in c['copied_and_hash_verified'] if not e['bytes']]
    assert 'retro/snes-mvp/saves/game-a27f1c7a-3145728.srm' in zero
    assert 'retro/snes-mvp/saves/failure-503-14018869000-session.txt' in zero
    assert digest(RETURN/'snes-mvp/last-run.log')==digest(ROOT/'device-evidence/snes-mvp-return-20261006T125627Z/snes-mvp/last-run.log')
    start=(RETURN/'snes-mvp/startup.log').read_text()
    assert 'SNES MVP 1.18' in start and 'splash handoff complete active_pids=none' in start
    check=(RETURN/'chkdsk-before-repair.txt').read_text(encoding='utf-8')
    assert 'first allocation unit is not valid' in check and 'without the /F' in check
    data={'version':'1.18','archive_utc':'2026-10-09T14:43:58Z','local_date':'2026-10-09 America/Chicago',
          'mvp_files_hash_verified':51,'lab_files_hash_verified':49,'card_writes':0,
          'game_and_lab_unarmed':True,'installed_release_matches':release_match,
          'stock_and_hook_hashes_match':True,'all_retained_snapshots_match':True,
          'read_errors':[{'card_path':e['card_path'],'operation':e['operation'],'winerror':e['winerror']} for e in c['read_errors']],
          'zero_byte_files':zero,'private_full_card_backup':{'files':len(full['copied_and_hash_verified']),
            'bytes':sum(e['bytes'] for e in full['copied_and_hash_verified']),'unreadable_entries':2,
            'all_readable_files_hash_verified':True},
          'user_result':'Terra Magitek armor Bio Blast again returns to our launcher; audio descriptor failed message reported',
          'fresh_startup':'1.18 child503, launch request at14.002s, library returns at53.490s; successful splash handoff',
          'capture_limits':'Fresh unique PCM/session records, latest PCM trace, current SRAM and latest session are zero bytes. last-run.log is stale 1.16, byte-identical to prior archive. There are no fresh effect timings or PCM transactions to price the color cache or identify this audio stop.',
          'filesystem':'Read-only Windows FAT32 check reports two invalid first allocation units, about1472KB of lost chains. No repair was performed. This establishes metadata corruption, not a defective physical card or the cause of EBADFD.',
          'next_action':'Backed-up FAT repair with lost-chain recovery requires consent. Recover any fresh reports/SRAM; restore only a verified prior SRAM if recovery cannot supply it. Require a clean filesystem before installation/re-arm. No unsupported core/audio tweak.'}
    private=RETURN/'analysis.json';private.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    publisher=load('publish-snes-1.18.py');manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes()
    previous=json.loads(raw)['entries'];assert not any(e['published'].startswith(PREFIX) for e in previous)
    for e in previous:assert digest(ROOT/e['published'])==e['published_sha256']
    selected={'analysis.json':private,'startup.log':RETURN/'snes-mvp/startup.log',
              'last-progress.txt':RETURN/'snes-mvp/last-progress.txt',
              'chkdsk-before-repair.txt':RETURN/'chkdsk-before-repair.txt'}
    additions=[]
    for name,source in selected.items():
        original=source.read_bytes();output=publisher.public_text(original)
        for forbidden in (b'GITHUB_TOKEN',b'Bearer ',b'github_pat_',b'ghp_',b'C:\\Users',b'.codex/attachments'):
            assert forbidden not in output,(name,forbidden)
        target=ROOT/PREFIX/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(output)
        additions.append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
                          'source_sha256':sha256(original).hexdigest(),'published_sha256':sha256(output).hexdigest(),
                          'bytes':len(output),'normalized':original!=output})
    manifest.write_bytes(publisher.append_manifest(raw,additions))
    print(json.dumps(data,indent=2))
if __name__=='__main__':publish()
