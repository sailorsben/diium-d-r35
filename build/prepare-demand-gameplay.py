"""Stage qualified demand-v3 gameplay privately; no card writes."""
from pathlib import Path
from hashlib import sha256
import json, shutil, struct, sys, zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-gameplay-private-v1'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 assert not OUT.exists();OUT.mkdir();(OUT/'saves').mkdir()
 core=ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so'
 runner=ROOT/'build/demand-private-v1/owned-output-runner'
 assert digest(core)=='1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8'
 rp=json.loads((ROOT/'build/demand-private-v1/runtime-proof.json').read_text())
 assert rp['passed'] and digest(runner)==rp['runner_sha256']
 for n in ('qualification.json','native-proof.json','transition-proof.json'):
  p=ROOT/'build/demand-visible-private-v3'/n
  if p.exists():assert json.loads(p.read_text())['passed']
 shutil.copy2(core,OUT/'plus-a7.so');shutil.copy2(runner,OUT/'snes-mvp')
 s=(ROOT/'build/quick-profile-private-v1/launch.sh').read_text()
 s=s.replace('BASE=/usr/retro/snes-profile1','BASE=${D35_MVP_BASE:-/usr/retro/snes-demand-gameplay1}')
 s=s.replace('TRIGGER=/usr/retro/snes-mvp','TRIGGER=${D35_GAMEPLAY_TRIGGER:-/usr/retro/snes-mvp}')
 s=s.replace('1.19-profile1','1.19-demand-gameplay1')
 old='IFS= read -r D35_COST_ROM < "$BASE/ROM-PATH.txt" || exit 1\n[ -f "$D35_COST_ROM" ] || exit 1\n"$BASE/ability-suite" "$BASE" "$D35_COST_ROM"'
 assert old in s
 s=s.replace(old,'"$BASE/snes-mvp" --base "$BASE" --core "$BASE/plus-a7.so" --saves "$BASE/saves"')
 (OUT/'launch.sh').write_text(s,encoding='utf-8',newline='\n')
 (OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /bin/sh /usr/retro/snes-demand-gameplay1/launch.sh\n',newline='\n')
 source=archive/'retro/snes-confuser-gameplay1/saves'
 for p in sorted(source.iterdir()):
  if p.name.endswith(('.srm','.srm.bak')):shutil.copy2(p,OUT/'saves'/p.name)
 original=source/'game-a27f1c7a-3145728-core-5cb51346-798296.state'
 raw=original.read_bytes();assert raw[:8]==b'D35MVP01'
 assert len(raw)==40+struct.unpack_from('<I',raw,28)[0]
 assert zlib.crc32(raw[40:])&0xffffffff==struct.unpack_from('<I',raw,32)[0]
 assert struct.unpack_from('<II',raw,20)==(0x5cb51346,798296)
 cb=core.read_bytes();head=bytearray(raw[:40]);crc=zlib.crc32(cb)&0xffffffff
 struct.pack_into('<II',head,20,crc,len(cb))
 name=f'game-a27f1c7a-3145728-core-{crc:08x}-{len(cb)}.state'
 (OUT/'saves'/name).write_bytes(head+raw[40:])
 p={'version':'1.19-demand-gameplay1','archive':archive.name,'authorization':'User explicitly requested Push it to I: after the offline candidate was completed.',
 'manual_controls':True,'forced_replay':False,'production_gate_passed':False,'A7_saving_measured':False,
 'core_sha256':digest(core),'runner_sha256':digest(runner),'snapshot_source':original.relative_to(archive).as_posix(),
 'snapshot_source_sha256':digest(original),'snapshot_payload_sha256':sha256(raw[40:]).hexdigest(),'snapshot_name':name,
 'core_crc32':f'{crc:08x}','core_bytes':len(cb),'runtime_report_version':'1.19; identify experiment through wrapper and core CRC',
 'payload_hashes':{f.relative_to(OUT).as_posix():digest(f) for f in OUT.rglob('*') if f.is_file()}}
 (OUT/'prepared.json').write_text(json.dumps(p,indent=2)+'\n')
 print(json.dumps({'prepared':True,'version':p['version'],'snapshot_header_only_changed':True,'card_writes':0}))
if __name__=='__main__':main(Path(sys.argv[1]))
