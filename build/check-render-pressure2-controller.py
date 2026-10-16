"""Cross-compile actual ownership seam and reject reintroduced double finish."""
from pathlib import Path
from hashlib import sha256
import json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/render-pressure2-private'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def run(args,timeout=90):
 r=subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
 return r
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def main():
 case=OUT/'controller-seam';assert not case.exists();case.mkdir()
 source=ROOT/'build/render-pressure2.c';text=source.read_text()
 marker='/* audio_pipe_stop(1) drains in the joined audio owner; never finish twice. */'
 assert text.count(marker)==1
 bug=case/'double-finish.c';bug.write_text(text.replace(marker,'if(!failed && board_audio_finish()<0)failed=1;'),encoding='utf-8',newline='\n')
 compiler=['arm-linux-gnueabihf-gcc','-DD35_PLUS_A7','-DD35_NATIVE_PCM','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-Ibuild','-Ibuild/render-pressure2-private/runner','-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o','build/check-render-pressure2-controller.c','build/render-pressure2-private/runner/audio-owner.c','-Lbuild/sysroot/lib','-Wl,--no-as-needed','-l:libpthread-2.30.so','-l:libc-2.30.so','-l:libgcc_s.so.1','-l:ld-2.30.so']
 for label in ['good','reintroduced_bug']:
  exe=case/label
  args=compiler+(['-DPRESSURE_CONTROLLER="render-pressure2-private/controller-seam/double-finish.c"'] if label=='reintroduced_bug' else [])+['-o',exe.relative_to(ROOT).as_posix()]
  r=run(args);assert r.returncode==0,(r.stdout,r.stderr)
  dest=case/(label+'-results');dest.mkdir()
  r=run(['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib',exe.relative_to(ROOT).as_posix(),dest.relative_to(ROOT).as_posix()])
  assert r.returncode==(0 if label=='good' else 10),(label,r.returncode,r.stdout,r.stderr)
  if label=='good':
   for i in range(6):
    result=kv(dest/f'phase-{i:03d}/result.txt')
    assert result['failed']==('1' if i==2 else '0')
    assert result['load_events']==('2' if i>=3 else '0')
    assert result['completed']==('60' if i>=3 else '5')
   assert kv(dest/'phase-002/result.txt')['audio_error']=='77'
 result=dict(passed=True,actual_threaded_audio_owner=True,single_finish_success=True,
             finish_failure_propagates=True,reintroduced_double_finish_rejected=True,
             bursts_executed=6,device_backend='deterministic fake; no PCM/DMA/performance claim',
             sources={p.relative_to(ROOT).as_posix():digest(p) for p in [Path(__file__),ROOT/'build/check-render-pressure2-controller.c',source,OUT/'runner/audio-owner.c']})
 (OUT/'controller-qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
