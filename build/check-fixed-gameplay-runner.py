"""Boot all five backup games in the exact qualified frontend with the fixed core."""
from pathlib import Path
from hashlib import sha256
import json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-fixes-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def main():
 binary=ROOT/'build/presentation-runtime-private-v1/snes-mvp';q=json.loads((binary.parent/'qualification.json').read_text());assert digest(binary)==q['runner_sha256'];core=OUT/'core/snes9x2005_plus_libretro.so';results=[]
 for game in range(5):
  for policy in (0,1):
   folder=OUT/f'runner-{game}-{policy}';folder.mkdir();saves=folder/'saves';saves.mkdir();calls=2400 if game==4 else 600
   args=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib',str(binary),'--mock','--rom',str(ROOT/f'build/multigame-private-v3/game-{game}.sfc'),'--core',str(core),'--saves',str(saves)]
   env={**os.environ,'D35_MVP_FRAMES':str(calls),'D35_MVP_NO_PACING':'1','D35_FULL_HOST_FIXTURE':'1','D35_PRESENTATION_POLICY':str(policy)}
   with (folder/'run.log').open('w') as f:r=subprocess.run(args,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
   s=kv(saves/'last-session.txt');passed=r.returncode==0 and int(s['runs'])==int(s['rendered_frames'])==int(s['video_submitted'])==calls and not s['error'] and s['mock_backend']=='1' and s['audio_remaining_frames']==s['audio_cleared_frames']=='0' and int(s['output_accepted_frames_including_priming'])==int(s['resampled_enqueued_frames'])+int(s['priming_silence_frames'])
   results.append({'game':game,'policy':policy,'passed':passed,'returncode':r.returncode,'calls':calls,'session':s,'log_sha256':digest(folder/'run.log'),'session_sha256':digest(saves/'last-session.txt')});print('RUNNER',game,policy,passed,flush=True)
 (OUT/'runner-result.json').write_text(json.dumps({'physical':False,'production_gate':False,'runner_sha256':digest(binary),'core_sha256':digest(core),'results':results,'source_sha256':digest(Path(__file__))},indent=2)+'\n')
if __name__=='__main__':main()
