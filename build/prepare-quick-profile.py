"""Owned four-epoch profiling runner; renderer binary is reused unchanged."""
from pathlib import Path
from hashlib import sha256
import json, shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/quick-profile-private-v1'
OLD=ROOT/'build/combined-test-private-v1'
AUTH="Build a quick test and load I so we can get some benchmark numbers. This doesn't have be exhaustive. I just want to move the needle here in terms of what we know."
def digest(p):return sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists()
 q=json.loads((OLD/'verification.json').read_text())
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for name,h in q[group].items():assert digest(ROOT/name)==h,name
 OUT.mkdir();shutil.copytree(OLD/'runner',OUT/'runner');(OUT/'cores').mkdir()
 for name in ('control','profile'):shutil.copy2(OLD/'cores/combined.so',OUT/f'cores/{name}.so')
 for p in OLD.glob('*.h'):shutil.copy2(p,OUT/p.name)
 oldplan=json.loads((OLD/'plan.json').read_text());cases=[c for c in oldplan['cases'] if c['seq'] in (1,8)]
 assert len(cases)==2
 for c in cases:
  src=OLD/f"cases/{c['seq']:03d}";dest=OUT/f"cases/{c['seq']:03d}";dest.mkdir(parents=True)
  for name in ('control','profile'):shutil.copy2(src/'combined.state',dest/f'{name}.state')
  for name in ('input.txt','expected.bin','case.json'):shutil.copy2(src/name,dest/name)
 for p in (OUT/'runner').glob('*.[ch]'):
  write(p,p.read_text().replace('1.19-combined1','1.19-profile1').replace('1.19-focus1','1.19-profile1'))
 p=OUT/'runner/runner.c';s=p.read_text()
 old='    /* No nested core/callback clocks in this complete-path comparison. */\n    p_profile_begin=NULL;p_profile_end=NULL;'
 assert old in s
 s=s.replace(old,'    if(!getenv("D35_QUICK_PROFILE")){p_profile_begin=NULL;p_profile_end=NULL;}\n    else if(!p_profile_begin||!p_profile_end){fail("Required core phase hooks unavailable");goto done;}')
 s=s.replace('    unsigned focus_active,focus_reason,focus_audio_calls,focus_video_calls;','    struct frame_cost quick_rows[1200];\n    unsigned quick_count;\n    unsigned focus_active,focus_reason,focus_audio_calls,focus_video_calls;')
 s=s.replace('            d35_focus_observe(&s.focus_policy,sample,f->wall,f->cpu);','            d35_focus_observe(&s.focus_policy,sample,f->wall,f->cpu);\n            if(s.quick_count<ARRAY_SIZE(s.quick_rows))s.quick_rows[s.quick_count++]=*f;')
 needle='    pcm_cost_flush(s.save_dir);pair_finish(s.save_dir,board_is_null(),s.failed);ability_finish(s.save_dir);'
 assert needle in s
 s=s.replace(needle,needle+'\n    quick_flush();')
 # Include after the s aggregate and existing CPU-clock declaration.
 needle='static void fail(const char *fmt, ...)';s=s.replace(needle,'#include "quick-profile.h"\n'+needle)
 s=s.replace('focus_profile_baseline_stride=64','focus_profile_baseline_stride=8')
 s=s.replace('focus_profile_hot_frames=96','focus_profile_hot_frames=0')
 write(p,s)
 write(OUT/'runner/focus-profile.h','''#ifndef D35_FOCUS_PROFILE_H
#define D35_FOCUS_PROFILE_H
#include <stdint.h>
struct d35_focus_policy { unsigned sequence,hot_remaining,triggers; };
static inline unsigned d35_focus_next(struct d35_focus_policy *p){return p->sequence++%8u==3u?1u:0u;}
static inline void d35_focus_observe(struct d35_focus_policy *p,unsigned sampled,uint64_t wall,uint64_t cpu){(void)p;(void)sampled;(void)wall;(void)cpu;}
#endif
''')
 shutil.copy2(ROOT/'build/quick-profile.h',OUT/'runner/quick-profile.h')
 p=OUT/'runner/pair-host.h';write(p,p.read_text().replace('#phase_clocks=disabled','#phase_clocks=1_in_8_only_when_D35_QUICK_PROFILE'))
 runs=[{'run':0,'fixture':1,'variant':'control','variant_id':0,'repeat':0},{'run':1,'fixture':1,'variant':'profile','variant_id':1,'repeat':0},{'run':2,'fixture':8,'variant':'profile','variant_id':1,'repeat':0},{'run':3,'fixture':8,'variant':'control','variant_id':0,'repeat':0}]
 header='struct full_run{unsigned fixture,variant,repeat;};\nstatic const char *full_variants[]={"control","profile"};\nstatic const struct full_run full_runs[]={{1,0,0},{1,1,0},{8,1,0},{8,0,0}};\n#define D35_FULL_RUNS 4u\n'
 write(OUT/'combined-identity.h',header)
 s=(ROOT/'build/combined-test-main.c').read_text().replace('1.19-combined1','1.19-profile1').replace('"1200"','"800"')
 s=s.replace('  setenv("D35_FULL_VARIANT",','  if(r->variant)setenv("D35_QUICK_PROFILE","1",1);else unsetenv("D35_QUICK_PROFILE");\n  setenv("D35_FULL_VARIANT",')
 write(OUT/'main.c',s)
 for name in ('launch.sh','dispatch.sh','ROM-PATH.txt'):
  write(OUT/name,(OLD/name).read_text().replace('snes-combined1','snes-profile1').replace('1.19-combined1','1.19-profile1'))
 plan={'version':'1.19-profile1','authorization':AUTH,'measurement_only':True,'production_gate_passed':False,'frameskip':False,'calls_per_run':800,'warmup_calls':120,'period_ns':16688154.5,'target_ns':13350523.6,'runs':runs,'variants':['control','profile'],'cases':cases,'cores':{n:{'sha256':digest(OUT/f'cores/{n}.so'),'crc32':oldplan['cores']['combined']['crc32']} for n in ('control','profile')},'nominal_minutes':4*800*16.6881545/60000,'sampling':'fixed 1 in 8 calls, frame index mod 8 == 3; no adaptive trigger','limits':['PPU and APU inclusive CPU regions, not inward tile kernel unit costs.','APU includes audio callback. PPU may include video callback; never sum nested regions blindly.','Unattributed residual includes SNES CPU, port-driven SPC, dispatch and observer work.','All observer costs remain included; aligned control differences are disturbance estimates, never calibration subtraction.','800 calls cap includes known 392-549 failure/peak interval; early native faults may truncate it.']}
 write(OUT/'plan.json',json.dumps(plan,indent=2)+'\n')
 s=(ROOT/'build/build-combined-test.sh').read_text().replace('build/combined-test-private-v1','build/quick-profile-private-v1').replace('-DD35_NATIVE_PCM','-DD35_FOCUS_PROFILE -DD35_NATIVE_PCM')
 start=s.index('arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU');end=s.index('arm-linux-gnueabihf-readelf',start);s=s[:start]+s[end:]
 write(ROOT/'build/build-quick-profile.sh',s.replace('cores/combined.so','cores/control.so').replace('Built three-core combined measurement suite','Built four-epoch quick CPU profile'))
 print('Prepared four 800-call epochs; unchanged core; no card writes')
if __name__=='__main__':main()
