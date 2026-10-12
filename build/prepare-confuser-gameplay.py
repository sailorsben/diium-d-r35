"""Explicitly authorized isolated gameplay qualification; production stays intact."""
from pathlib import Path
from hashlib import sha256
import json,re,shutil,struct,sys,zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/confuser-gameplay-private-v1'
archive=Path(sys.argv[1]).resolve();assert archive.is_relative_to(ROOT/'device-evidence')
assert not OUT.exists();OUT.mkdir()
def digest(p):return sha256(p.read_bytes()).hexdigest()
a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
analysis=json.loads((ROOT/'build/confuser-private-v1/analysis.json').read_text())
assert analysis['output_comparison_frames']==10800 and not analysis['hardware_prices_measured']
for n,h in analysis['source_and_capture_hashes'].items():assert digest(ROOT/n)==h,n
origin=ROOT/'build/a7-pair-private-v1/core'
assert digest(origin/'snes9x2005_plus_libretro.so')=='ee0b241c3b7c561e76efbedbbdcf37bf8e104bb6754d7b0493c3ed4774172155'
core=OUT/'core';shutil.copytree(origin,core,ignore=shutil.ignore_patterns('.git','*.o','*.so'))
window=(ROOT/'build/confuser-private-v1/bg3-window/core/source/a7_window.h').read_text()
window=window.replace('#include "confuser.h"\n','').replace('extern unsigned long long d35_hyp[128];\n','')
window=re.sub(r'\+\+d35_(?:hyp|conf)\[\d+\];','',window)
window=re.sub(r'd35_hyp\[\d+\]\s*\+=.*?;','',window)
assert 'd35_conf' not in window and 'd35_hyp' not in window
(core/'source/a7_window.h').write_text(window,newline='\n')
p=core/'source/gfx.c';s=p.read_text()
old='bg==0 && d35_window_fetch(Y,';assert s.count(old)==1;s=s.replace(old,'d35_window_fetch(bg,Y,')
old='(bg==0 && !d35_window_same(Y,Y+Lines))';assert s.count(old)==1
s=s.replace(old,'(d35_window_is_target(bg) && !d35_window_same(Y,Y+Lines))');p.write_text(s,newline='\n')
p=core/'source/a7_tile.h';s=p.read_text();old='    uint8x8_t fixed_mask=vceq_u8(sd,vdup_n_u8(1));';assert s.count(old)==1
s=s.replace(old,'''    if(mode==2 && !vget_lane_u64(vreinterpret_u64_u8(
        vbic_u8(active,vcgt_u8(sd,vdup_n_u8(1)))),0))
        return d35_add_half(color,vld1q_u16(sub));
'''+old);p.write_text(s,newline='\n')
assert not any(any(x in p.read_text(errors='ignore') for x in ('d35_census','d35_hyp','d35_conf_pc','d35_conf[')) for p in core.glob('source/*.[ch]'))
normal=json.loads((ROOT/'releases/snes-mvp-1.19/manifest.json').read_text())
runner=ROOT/'releases/snes-mvp-1.19/snes-mvp';assert digest(runner)==normal['binary_sha256']
shutil.copy2(runner,OUT/'snes-mvp')
s=(ROOT/'releases/snes-mvp-1.19/launch.sh').read_text()
old='BASE=${D35_MVP_BASE:-/usr/retro/snes-mvp}';assert s.count(old)==1
s=s.replace(old,'BASE=${D35_MVP_BASE:-/usr/retro/snes-confuser-gameplay1}\nTRIGGER=${D35_GAMEPLAY_TRIGGER:-/usr/retro/snes-mvp}')
assert s.count('"$BASE/armed"')==2
s=s.replace('"$BASE/armed"','"$TRIGGER/armed"').replace('SNES MVP 1.19 native PCM startup','SNES MVP 1.19-confuser-gameplay1 native PCM startup')
(OUT/'launch.sh').write_text(s,newline='\n')
(OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /usr/retro/snes-confuser-gameplay1/launch.sh\n',newline='\n')
# Preserve the latest separate gameplay progress, including the user's SRAM.
source=archive/'retro/snes-combined-gameplay1/saves';saves=OUT/'saves';saves.mkdir()
copied={}
for p in sorted(source.iterdir()):
    if p.name.endswith(('.srm','.srm.bak')):shutil.copy2(p,saves/p.name);copied[p.name]=digest(p)
original=source/'game-a27f1c7a-3145728-core-b77a9eb3-794156.state'
raw=original.read_bytes();assert raw[:8]==b'D35MVP01'
assert len(raw)==40+struct.unpack_from('<I',raw,28)[0] and zlib.crc32(raw[40:])==struct.unpack_from('<I',raw,32)[0]
assert struct.unpack_from('<II',raw,20)==(0xb77a9eb3,794156)
(OUT/'snapshot-source.state').write_bytes(raw)
prepared={'version':'1.19-confuser-gameplay1','archive':archive.name,'regular_runner_sha256':digest(runner),
 'snapshot_source':original.relative_to(archive).as_posix(),'snapshot_source_sha256':digest(original),
 'snapshot_payload_sha256':sha256(raw[40:]).hexdigest(),'copied_sram_sha256':copied,
 'manual_controls':True,'forced_replay':False,'original_progress_modified':False,
 'hardware_saving_measured':False,'production_gate_passed':False,
 'authorization':'User explicitly requested Load it to I after missing A7 prices were disclosed; separate experimental qualification only'}
(OUT/'prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
print('Prepared counter-free isolated Confuser candidate and latest separate test progress')
