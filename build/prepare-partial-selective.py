"""Refine register-pressure issue: snapshot/sparse plain rows only, no card."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/partial-selective-private-v1'
def main():
 assert not OUT.exists();OUT.mkdir();core=OUT/'selective'
 shutil.copytree(ROOT/'build/common-band-private-v3/core',core,ignore=shutil.ignore_patterns('*.o','*.so'))
 shutil.copy2(ROOT/'build/partial-merge-selective.h',core/'source/a7_common_batch.h');shutil.copy2(ROOT/'build/partial-merge-kernels.h',core/'source/a7_partial_kernels.h');shutil.copy2(ROOT/'build/common-band-private-v3/ordinary-compare.c',OUT/'compare.c')
 s=(ROOT/'build/build-partial-candidates.sh').read_text().replace('partial-candidates-private-v1','partial-selective-private-v1').replace('for variant in local sparse;','for variant in selective;');(ROOT/'build/build-partial-selective.sh').write_text(s,newline='\n');print('Prepared selective plain-row refinement; no card access')
if __name__=='__main__':main()
