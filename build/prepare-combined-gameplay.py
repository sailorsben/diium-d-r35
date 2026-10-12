"""Prepare manual qualification with exact measured core and regular1.19 runner."""
from pathlib import Path
from hashlib import sha256
import json,shutil,struct,sys,zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/combined-gameplay-private-v1'
archive=Path(sys.argv[1]).resolve();assert archive.is_relative_to(ROOT/'device-evidence')
assert not OUT.exists();OUT.mkdir()
pair=json.loads((ROOT/'build/a7-pair-private-v1/verification.json').read_text())
returned=json.loads((ROOT/'evidence/2026-10-11/a7-pair1-return/analysis.json').read_text())
assert returned['combined_complete_passes']==returned['baseline_failed_passes']==6
normal=json.loads((ROOT/'releases/snes-mvp-1.19/manifest.json').read_text())
def digest(p):return sha256(p.read_bytes()).hexdigest()
runner=ROOT/'releases/snes-mvp-1.19/snes-mvp';core=ROOT/'build/a7-pair-private-v1/combined.so'
assert digest(runner)==normal['binary_sha256'] and digest(core)==pair['payload_hashes']['combined.so']
shutil.copy2(runner,OUT/'snes-mvp');shutil.copy2(core,OUT/'plus-a7.so')
wrapper=ROOT/'releases/snes-mvp-1.19/launch.sh';assert digest(wrapper)==normal['wrapper_sha256']
s=wrapper.read_text()
old='BASE=${D35_MVP_BASE:-/usr/retro/snes-mvp}';assert s.count(old)==1
s=s.replace(old,'BASE=${D35_MVP_BASE:-/usr/retro/snes-combined-gameplay1}\nTRIGGER=${D35_GAMEPLAY_TRIGGER:-/usr/retro/snes-mvp}')
assert s.count('"$BASE/armed"')==2
s=s.replace('"$BASE/armed"','"$TRIGGER/armed"').replace('SNES MVP 1.19 native PCM startup','SNES MVP 1.19-combined-gameplay1 native PCM startup')
(OUT/'launch.sh').write_text(s,newline='\n')
(OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /usr/retro/snes-combined-gameplay1/launch.sh\n',newline='\n')
saves=OUT/'saves';saves.mkdir()
source=archive/'retro/snes-mvp/saves';copied={}
for p in sorted(source.iterdir()):
    if p.name.endswith(('.srm','.srm.bak')):
        shutil.copy2(p,saves/p.name);copied[p.name]=digest(p)
original=source/'game-a27f1c7a-3145728-core-3d35ed49-789764.state'
raw=original.read_bytes()
assert raw[:8]==b'D35MVP01' and len(raw)==40+struct.unpack_from('<I',raw,28)[0]
assert struct.unpack_from('<II',raw,20)==(int(normal['core_crc32'],16),normal['core_bytes'])
assert zlib.crc32(raw[40:])==struct.unpack_from('<I',raw,32)[0]
crc=zlib.crc32(core.read_bytes());head=bytearray(raw[:40]);struct.pack_into('<II',head,20,crc,core.stat().st_size)
state_name=f'game-a27f1c7a-3145728-core-{crc:08x}-{core.stat().st_size}.state'
(saves/state_name).write_bytes(head+raw[40:]);assert (saves/state_name).read_bytes()[40:]==raw[40:]
prepared={'version':'1.19-combined-gameplay1','archive':archive.name,'regular_runner_sha256':digest(runner),
    'core_sha256':digest(core),'core_crc32':f'{crc:08x}','core_bytes':core.stat().st_size,
    'snapshot_source':original.relative_to(archive).as_posix(),'snapshot_source_sha256':digest(original),
    'snapshot_payload_sha256':sha256(raw[40:]).hexdigest(),'snapshot_name':state_name,'copied_sram_sha256':copied,
    'manual_controls':True,'forced_replay':False,'original_progress_modified':False}
(OUT/'prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
print(json.dumps({'prepared':True,'version':prepared['version'],'same_measured_core':True,'manual_controls':True,'snapshot_header_only_changed':True},indent=2))
