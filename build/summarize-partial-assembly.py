"""Record code-generation risks, never convert instructions/stack to A7 time."""
from pathlib import Path
from hashlib import sha256
import json,re
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/partial-selective-private-v1'
def main():
 result={}
 for variant,folder in [('baseline','build/common-band-private-v3'),('local','build/partial-candidates-private-v1'),('sparse','build/partial-candidates-private-v1'),('selective','build/partial-selective-private-v1')]:
  for mode in (0,1,3):
   p=ROOT/folder/(f'asm-d35_band_{mode}.txt' if variant=='baseline' else f'asm-{variant}-{mode}.txt');lines=p.read_text().splitlines();instructions=[]
   for line in lines:
    m=re.match(r'\s*[0-9a-f]+:\s+[0-9a-f]{8}\s+(\S+)',line)
    if m and not m[1].startswith('.'):instructions.append(line)
   result[f'{variant}_{mode}']={'static_instructions_excluding_literal_pool':len(instructions),'prologue':[l.strip() for l in lines if re.search(r'\b(push|vpush)\b|sub\s+sp, sp, #',l)][:3],'asm_sha256':sha256(p.read_bytes()).hexdigest()}
 (OUT/'assembly-summary.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded static assembly and register/stack conditions; no timing inference')
if __name__=='__main__':main()
