"""Fresh matched physical FFVI measurement package; no card access."""
from pathlib import Path
from hashlib import sha256
import json, shutil, struct, zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/presentation-ffvi-private-v1'
OLD=ROOT/'build/draw-order-test-private-v1'
PRODUCT=ROOT/'build/presentation-runtime-private-v1'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def write(p,s): p.write_text(s,encoding='utf-8',newline='\n')
def edit(p,a,b):
 s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));write(p,s.replace(a,b))
def main():
 assert not OUT.exists()
 q=json.loads((OLD/'verification.json').read_text());assert q['passed']
 pq=json.loads((PRODUCT/'qualification.json').read_text());assert pq['passed']
 for n,h in q['source_hashes'].items():assert digest(ROOT/n)==h,n
 for n,h in pq['generated_sources'].items():assert digest(PRODUCT/n)==h,n
 OUT.mkdir();rt=OUT/'runner';rt.mkdir()
 for p in (OLD/'runner').glob('*.[ch]'):shutil.copyfile(p,rt/p.name)
 shutil.copyfile(ROOT/'build/plus-a7-profile.h',OUT/'plus-a7-profile.h')
 for n in ('board.c','board.h'):shutil.copyfile(PRODUCT/'runner'/n,rt/n)
 # Transplant the exact production policy sections into the established full
 # 1200-frame measurement runner; diagnostics are identical in both policies.
 product=(PRODUCT/'runner/runner.c').read_text();p=rt/'runner.c'
 edit(p,'    bool have_previous, av_changed;',product[product.index('    bool have_previous, av_changed;'):product.index('    int16_t previous')].rstrip())
 edit(p,'    began=board_now_ns();\n    if(board_video_submit', '''    ++s.rendered;
    if(s.skip_presentation) { ++s.presentation_skipped; return; }
    began=board_now_ns();
    if(board_video_submit''')
 start=product.index('    s.presentation_policy=1;');end=product.index('    if(!ensure_directory(save_dir))',start)
 edit(p,'    if(!ensure_directory(save_dir))',product[start:end]+'    if(!ensure_directory(save_dir))')
 start=product.index('        { uint64_t wait=board_now_ns();\n          int credit=');end=product.index('        s.buttons=board_poll_input()',start)
 edit(p,'        if(board_video_reserve()<0) { fail("Display queue stalled: %s",board_last_error()); break; }\n',product[start:end])
 start=product.index('        if(p_output_acquire){\n');end=product.index('        if(p_profile_begin)',start)
 edit(p,'        if(p_output_acquire){size_t bytes=0;void *target=board_video_target(&bytes);p_output_acquire(target,bytes);}\n',product[start:end])
 edit(p,'    if(s.core) dlclose(s.core);','    if(s.core) dlclose(s.core);\n    free(s.render_scratch);s.render_scratch=NULL;')
 start=product.index('      "presentation_policy=');end=product.index('      "audio_cleared_frames=',start)
 edit(p,'      "audio_cleared_frames=',product[start:end]+'      "audio_cleared_frames=')
 edit(p,'      (unsigned long long)s.audio_cleared,(unsigned long long)s.audio_remaining,', '''      s.presentation_policy,(unsigned long long)s.rendered,
      (unsigned long long)s.presentation_skipped,(unsigned long long)s.presentation_try_ns,
      (unsigned long long)s.audio_cleared,(unsigned long long)s.audio_remaining,''')
 edit(p,'#include "pair-host.h"','#include "pair-host.h"\n#include "../presentation-burst.h"')
 edit(p,'    save_ready=false;pair_begin();','    save_ready=false;pair_begin();presentation_burst_begin();')
 edit(p,'        p_retro_run();','        p_retro_run();\n        presentation_burst((unsigned)s.runs);')
 edit(p,'step_start,s.generated);','step_start,s.generated,s.rendered,s.presentation_skipped,s.presentation_try_ns,presentation_load_events,presentation_load_cpu);')
 write(p,p.read_text().replace('1.19-draw-order1','1.19-presentation-ffvi1'))
 shutil.copyfile(ROOT/'build/presentation-burst.h',OUT/'presentation-burst.h')
 p=rt/'pair-host.h'
 edit(p,'    unsigned frame,pointer_valid;','    unsigned frame,pointer_valid;\n    uint64_t rendered,skipped,reservation,load_events,load_cpu;')
 edit(p,'uint64_t step,uint64_t generated) {','uint64_t step,uint64_t generated,uint64_t rendered,uint64_t skipped,uint64_t reservation,uint64_t load_events,uint64_t load_cpu) {')
 edit(p,'    r->before_khz=','    r->rendered=rendered;r->skipped=skipped;r->reservation=reservation;r->load_events=load_events;r->load_cpu=load_cpu;\n    r->before_khz=')
 edit(p,'copied_payload_bytes\\n','copied_payload_bytes,rendered,skipped,reservation_ns,load_events,load_cpu_ns\\n')
 edit(p,'%u,%llu,%llu\\n",','%u,%llu,%llu,%llu,%llu,%llu,%llu,%llu\\n",')
 edit(p,'(unsigned long long)r->video.copied_payload_bytes);','(unsigned long long)r->video.copied_payload_bytes,(unsigned long long)r->rendered,(unsigned long long)r->skipped,(unsigned long long)r->reservation,(unsigned long long)r->load_events,(unsigned long long)r->load_cpu);')
 write(p,p.read_text().replace('1.19-draw-order1','1.19-presentation-ffvi1'))
 p=rt/'combined-headroom.h'
 edit(p,'final.submitted==1200&&final.flipped==1200','pair_rows[1199].rendered==1200&&final.submitted+pair_rows[1199].skipped==1200&&final.flipped==final.submitted')
 write(p,p.read_text().replace('frameskip=0','emulation_frameskip=0\\npresentation_skips=see_frames_csv').replace('1.19-draw-order1','1.19-presentation-ffvi1'))
 # Headers only retagged; payload and CRC remain unchanged, original preserved.
 core=PRODUCT/'plus-a7.so';assert digest(core)==pq['core_sha256'];shutil.copyfile(core,OUT/'plus-a7.so')
 plan=json.loads((OLD/'plan.json').read_text());runs=[]
 for repeat in range(4):
  policy=[0,1,1,0][repeat]
  for c in plan['cases'] if repeat%2==0 else list(reversed(plan['cases'])):
   runs.append(dict(run=len(runs),fixture=c['seq'],name=c['name'],policy=policy,repeat=repeat,load_ms=0,block='regression'))
 for load in (24,48):
  for repeat,policy in enumerate((0,1,1,0)):
   runs.append(dict(run=len(runs),fixture=0,name=plan['cases'][0]['name'],policy=policy,repeat=repeat,load_ms=load,block='burst'))
 assert len(runs)==80
 for c in plan['cases']:
  src=ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}";dest=OUT/f"cases/{c['seq']:03d}";dest.mkdir(parents=True)
  raw=(src/'scene.state').read_bytes();assert digest(src/'scene.state')==c['state_sha256']
  assert zlib.crc32(raw[40:])&0xffffffff==struct.unpack_from('<I',raw,32)[0]
  head=bytearray(raw[:40]);cb=core.read_bytes();struct.pack_into('<II',head,20,zlib.crc32(cb)&0xffffffff,len(cb))
  (dest/'scene.state').write_bytes(head+raw[40:])
  for n in ('input.txt','expected.bin','case.json'):shutil.copyfile(src/n,dest/n)
  assert digest(dest/'input.txt')==c['input_sha256'] and digest(dest/'expected.bin')==c['expected_sha256']
 header='struct ffvi_run {unsigned fixture,policy,repeat,load_ms;};\n'
 header+='static const struct ffvi_run ffvi_runs[]={'+','.join('{%d,%d,%d,%d}'%(r['fixture'],r['policy'],r['repeat'],r['load_ms']) for r in runs)+'};\n'
 header+='static const char *spell_names[]={'+','.join('"'+c['name']+'"' for c in plan['cases'])+'};\n'
 write(OUT/'identity.h',header)
 shutil.copyfile(ROOT/'build/presentation-ffvi-main.c',OUT/'main.c')
 shutil.copyfile(OLD/'ROM-PATH.txt',OUT/'ROM-PATH.txt')
 wrapper=(ROOT/'build/render-pressure3-private/launch.sh').read_text().replace('/usr/retro/render-pressure3','/usr/retro/snes-presentation-ffvi1').replace('render-pressure3 wrapper','presentation-ffvi1 wrapper')
 wrapper=wrapper.replace('  case "$UART" in', '  { cat "$PROC/uptime" "$PROC/interrupts" 2>&1; } > "$OUT/irq-$1.txt"\n  case "$UART" in')
 wrapper=wrapper.replace('"$LAB/render-pressure" --supervise --output "$OUT" > "$OUT/console.log" 2>&1', '''IFS= read -r ROM < "$LAB/ROM-PATH.txt" || exit 1
[ -f "$ROM" ] || exit 1
RAMLOG="/tmp/presentation-ffvi-$$.log"
"$LAB/ffvi-suite" --supervise "$OUT" "$LAB" "$ROM" > "$RAMLOG" 2>&1''')
 wrapper=wrapper.replace('RESULT=$?\n','RESULT=$?\ncp "$RAMLOG" "$OUT/console.log" || RESULT=72\n')
 write(OUT/'launch.sh',wrapper);write(OUT/'dispatch.sh','#!/bin/sh\nexec /bin/sh /usr/retro/snes-presentation-ffvi1/launch.sh\n')
 plan={'version':'presentation-ffvi1','runs':runs,'cases':plan['cases'],'calls':1200,'period_ns':16688153,
       'core_sha256':digest(core),'burst_frames':[239,359,479,599,719,839,959],
       'nominal_minutes':80*1200*16688153/60e9,'deadline_minutes':35,
       'one_variable':'presentation policy; all core/state/input/audio/load work identical within each ABBA block',
       'measurement_only':True,'production_gate':False,'physical_result':'PENDING'}
 write(OUT/'plan.json',json.dumps(plan,indent=2)+'\n')
 frozen={n:h for n,h in q['source_hashes'].items()};frozen.update({str((PRODUCT/n).relative_to(ROOT)).replace('\\','/'):h for n,h in pq['generated_sources'].items()})
 write(OUT/'frozen.json',json.dumps(frozen,indent=2)+'\n')
 print('Prepared 80 matched FFVI epochs (72 original contexts + 8 burst cells); no card access')
if __name__=='__main__':main()
