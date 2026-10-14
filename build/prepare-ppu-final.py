"""Keep qualified v4 intact; force sparse math into constant-mode callers."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'build/ppu-refinements-private-v4'
OUT=ROOT/'build/ppu-refinements-private-v5'
def main():
 assert not OUT.exists();assert json.loads((OLD/'qualification.json').read_text())['passed']
 OUT.mkdir();frozen=json.loads((OLD/'frozen.json').read_text())
 for p in OLD.rglob('*'):
  if p.is_file() and p.suffix in ('.c','.h','.so','.json','.log'):frozen[p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
 (OUT/'frozen.json').write_text(json.dumps(frozen,indent=2)+'\n')
 for label in ('combined','combined-counted'):
  target=OUT/label;shutil.copytree(OLD/label,target,ignore=shutil.ignore_patterns('*.o','*.so'))
  p=target/'source/a7_ppu_math.h';s=p.read_text();a='static inline unsigned d35_sparse_math(';assert s.count(a)==1
  p.write_text(s.replace(a,'static inline __attribute__((always_inline)) unsigned d35_sparse_math('),newline='\n')
  p=target/'source/a7_common_batch.h';s=p.read_text();a='    FT(n==1?16:17);';assert s.count(a)==1
  p.write_text(s.replace(a,'    if(n<=2)FT(n==1?16:17); /* Keep legacy1/2 counters distinct from new shapes. */'),newline='\n')
 for name in ('compare','compare.c','demand-equivalence.c','seams.json'):shutil.copy2(OLD/name,OUT/name)
 script=(ROOT/'build/build-ppu-refinements.sh').read_text().replace('build/ppu-refinements-private-v4','build/ppu-refinements-private-v5')
 script=script.replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."')
 script=script.replace('for label in obj obj-counted shapes shapes-counted bulk bulk-counted combined combined-counted;','for label in combined combined-counted;')
 (OUT/'build.sh').write_text(script,newline='\n')
 print('Prepared final refinement: constant-mode sparse arithmetic inlined; previous qualified variants preserved')
if __name__=='__main__':main()
