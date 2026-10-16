"""Bounded backup-ROM regression; no backup/card changes, no A7 speed inference."""
from pathlib import Path
import csv,hashlib,json,os,subprocess,zipfile
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-private-v3'
NAMES=['SUPER MARIOWORLD','超级银河战士(汉化版)','F-ZERO','Star Fox','Rendering Ranger R2']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
 assert not OUT.exists(),'Preserve existing results';OUT.mkdir()
 games=[]
 for i,name in enumerate(NAMES):
  source=Path('E:/R35/002')/(name+'.zip')
  with zipfile.ZipFile(source) as z:
   files=[n for n in z.namelist() if n.lower().endswith(('.sfc','.smc','.fig','.bin'))];assert len(files)==1,(name,z.namelist())
   data=z.read(files[0]);target=OUT/f'game-{i}.sfc';target.write_bytes(data)
  headers=[]
  for offset in (0x7fc0,0xffc0,0x407fc0):
   if offset+32<=len(data):headers.append({'offset':offset,'title':data[offset:offset+21].decode('ascii',errors='replace'),'map_mode':data[offset+21],'type':data[offset+22],'region':data[offset+25]})
  games.append({'index':i,'backup_zip':str(source),'zip_sha256':digest(source),'zip_member':files[0],'ROM_sha256':digest(target),'ROM_bytes':len(data),'headers':headers})
 (OUT/'inputs.json').write_text(json.dumps(games,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps(games,ensure_ascii=True))
def qualify():
 assert os.name!='nt';games=json.loads((OUT/'inputs.json').read_text());assert not (OUT/'result.json').exists()
 ref=ROOT/'build/common-band-private-v3/plus-a7.so';core=ROOT/'build/presentation-ffvi-private-v1/plus-a7.so'
 assert digest(core)=='1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8'
 args=['arm-linux-gnueabihf-gcc','-DUSE_BLARGG_APU','-std=gnu99','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-Ibuild','-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o','build/check-multigame.c','-Lbuild/sysroot/lib','-Wl,--no-as-needed','-l:libdl-2.30.so','-l:libz.so.1','-l:libc-2.30.so','-l:libgcc_s.so.1','-o',str(OUT/'check')]
 with (OUT/'build.log').open('w') as f:subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 results=[]
 for game in games:
  i=game['index'];folder=OUT/f'game-{i}';folder.mkdir();rom=OUT/f'game-{i}.sfc';assert digest(rom)==game['ROM_sha256']
  cmd=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib',str(OUT/'check'),str(ref),str(core),str(rom),str(folder/'frames.csv'),str(i),str(folder)]
  try:
   with (folder/'run.log').open('w') as f:run=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=480)
   code=run.returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
  log=(folder/'run.log').read_text();passed=code==0 and 'PASS calls=6000' in log
  records=list(csv.DictReader((folder/'frames.csv').open())) if (folder/'frames.csv').exists() else []
  results.append({**game,'returncode':code,'passed':passed,'recorded_calls':len(records),'changed_pictures':sum(int(r['changed']) for r in records),'last_log_lines':log.splitlines()[-3:],'artifacts':{str(p.relative_to(OUT)):digest(p) for p in folder.iterdir() if p.is_file()}})
  print('RESULT',i,passed,code,log.splitlines()[-1:] ,flush=True)
 result={'version':'multigame1','physical':False,'A7_performance_evidence':False,'production_gate':False,'reference_core_sha256':digest(ref),'candidate_core_sha256':digest(core),'calls_per_game':6000,'state_check_period':30,'games':results,'source_hashes':{str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'build/check-multigame.c',ROOT/'build/check-multigame.py')},'limits':['QEMU checks correctness, not handheld throughput or audio reserve.','Direct/scratch/fallback targets exercise core output paths; display-worker scheduling is covered separately, not simulated here.','Scenes require screenshot inspection; scripted button counts alone do not establish gameplay coverage.','Reference core is the earlier common-band candidate, not independent hardware truth.']}
 (OUT/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print('COMPLETE',flush=True)
if __name__=='__main__':
 import sys
 prepare() if '--prepare' in sys.argv else qualify()
