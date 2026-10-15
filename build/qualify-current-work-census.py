"""Current-core mechanisms, not QEMU timings; output/state qualified replays."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json,os,statistics,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/current-work-private-v1'
FIELDS={0:'CPU_opcode_dispatches',1:'SPC_entries',2:'SPC_opcode_attempts',3:'SPC_port_reads',4:'SPC_port_writes',5:'SPC_end_frame_calls',6:'DSP_requested_clocks',7:'gaussian_interpolations',9:'decoded_tiles',10:'NEON_palette_preparations',11:'BG_draw_invocations',12:'OBJ_draw_invocations',13:'PPU_redraws',16:'main_RGB_writes',17:'overwritten_main_RGB_writes',18:'math_pixel_writes',19:'overwritten_math_writes',20:'surviving_math_owners',21:'foreground_pixels_missing_provenance',22:'sub_RGB_writes',23:'unsupported_layout',24:'plain_batch_row_visits',25:'math_batch_row_visits',26:'fallback_full_tile_row_visits',27:'batch_RGB_vector_expansions',28:'sparse_plain_pixel_stores',33:'overwritten_OBJ_pixels',34:'overwritten_BG0_pixels',35:'overwritten_BG1_pixels',36:'overwritten_BG2_pixels',37:'overwritten_BG3_pixels',41:'overwriting_OBJ_pixels',42:'overwriting_BG0_pixels',43:'overwriting_BG1_pixels',44:'overwriting_BG2_pixels',45:'overwriting_BG3_pixels',56:'backdrop_math_writes'}
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();(OUT/'exact').mkdir()
 cases=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text())['cases']
 selected=[c for c in cases if c['seq'] in (0,1,8,12,16,17)]
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(c):
  log=OUT/f"exact/{c['seq']:03d}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so'),str(OUT/'core/snes9x2005_plus_libretro.so'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
  s=log.read_text();assert 'PASS 1200 calls' in s
  rows=[list(map(int,l[8:].split(','))) for l in s.splitlines() if l.startswith('CURRENT ')]
  assert len(rows)==1200 and all(len(r)==65 for r in rows)
  assert all(r[1+21]==r[1+23]==0 for r in rows),'Untracked output invalidates provenance'
  assert all(r[1+18]-r[1+19]==r[1+20] for r in rows),'Math ownership identity'
  groups={'early':range(120,240),'full_warm':range(120,1200)}
  if c['seq'] in (1,12):groups.update(earlier_peak=range(384,416),late_peak=range(496,536))
  if c['seq']==8:groups['late_peak']=range(496,542)
  means={k:{name:statistics.mean(rows[i][1+j] for i in span) for j,name in FIELDS.items()} for k,span in groups.items()}
  print('PASS current-v3 work and exact graphics/PCM/state',c['name'],flush=True)
  return {'fixture':c['seq'],'name':c['name'],'calls':1200,'log_sha256':digest(log),'means':means}
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,selected))
 for n,h in json.loads((OUT/'frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 result={'passed':True,'observer_only':True,'raw_graphics_PCM_geometry_calls':7200,'normalized_state_every':30,'fields':FIELDS,'cases':results,'A7_time_claim':False,'QEMU_time_claim':False,'card_access':False,'core_sha256':digest(OUT/'core/snes9x2005_plus_libretro.so'),'oracle_sha256':digest(ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so')}
 (OUT/'qualification.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
