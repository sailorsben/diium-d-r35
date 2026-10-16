"""Exact presentation gameplay runner, both policies, private mock cold boots."""
from pathlib import Path
from hashlib import sha256
import json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-private-v3'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def main():
 assert os.name!='nt';binary=ROOT/'build/presentation-runtime-private-v1/snes-mvp';q=json.loads((binary.parent/'qualification.json').read_text());assert digest(binary)==q['runner_sha256']
 core=ROOT/'build/presentation-ffvi-private-v1/plus-a7.so';assert digest(core)==q['core_sha256'];results=[]
 for game in range(5):
  for policy in (0,1):
   folder=OUT/f'runner-{game}-{policy}';folder.mkdir();saves=folder/'saves';saves.mkdir()
   args=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib',str(binary),'--mock','--rom',str(OUT/f'game-{game}.sfc'),'--core',str(core),'--saves',str(saves)]
   env={**os.environ,'D35_MVP_FRAMES':'600','D35_MVP_NO_PACING':'1','D35_FULL_HOST_FIXTURE':'1','D35_PRESENTATION_POLICY':str(policy)}
   with (folder/'run.log').open('w') as f:r=subprocess.run(args,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
   session=kv(saves/'last-session.txt');passed=r.returncode==0 and session['runs']==session['rendered_frames']=='600' and not session['error'] and session['mock_backend']=='1'
   results.append({'game':game,'policy':policy,'passed':passed,'returncode':r.returncode,'session':session,'log_sha256':digest(folder/'run.log'),'session_sha256':digest(saves/'last-session.txt')});print('RUNNER',game,policy,passed,flush=True)
 result={'physical':False,'production_gate':False,'runner_sha256':digest(binary),'core_sha256':digest(core),'calls_per_cell':600,'results':results,'source_sha256':digest(Path(__file__)),'limits':['Mock board verifies actual frontend/runner/core/PCM software accounting and shutdown; not physical PCM, display credit, A7 costs, or gameplay.','No scripted input in these 600-call boot cells; gameplay evidence belongs to separately inspected comparator scenes.']}
 (OUT/'runner-result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
