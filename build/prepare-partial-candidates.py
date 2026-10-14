"""Prepare isolated exact row-state and sparse-pixel alternatives, never card."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/partial-candidates-private-v1'
def main():
 assert not OUT.exists();OUT.mkdir()
 for name in ('local','sparse'):
  core=OUT/name
  shutil.copytree(ROOT/'build/common-band-private-v3/core',core,ignore=shutil.ignore_patterns('*.o','*.so'))
  shutil.copy2(ROOT/f'build/partial-merge-{name}.h',core/'source/a7_common_batch.h')
  shutil.copy2(ROOT/'build/partial-merge-kernels.h',core/'source/a7_partial_kernels.h')
 shutil.copy2(ROOT/'build/common-band-private-v3/ordinary-compare.c',OUT/'compare.c')
 script=(ROOT/'build/build-common-band.sh').read_text();a=script.index('if [ ! -e');b=script.index("libs=",a);head=script[:a].replace('common-band-private-v3','partial-candidates-private-v1')
 build=script[script.index('(cd "$out/counted-core"'):script.index('\narm-linux-gnueabihf-gcc $flags',script.index('(cd "$out/counted-core"'))].replace('counted-core','$variant').replace('"$out/counted-build.log"','"$out/$variant-build.log"')
 tail=script[b:script.index("echo 'Built",b)];tail=tail.replace('"$out/ordinary-compare.c"','"$out/compare.c"')
 text=head+'for variant in local sparse; do\n'+build+'\ndone\n'+tail
 (ROOT/'build/build-partial-candidates.sh').write_text(text,newline='\n')
 print('Prepared two isolated candidate cores; no card access')
if __name__=='__main__':main()
