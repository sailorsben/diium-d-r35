"""Repeat only changed-combination integration; preserve qualified v2 trees."""
from pathlib import Path
import runpy,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-visible-private-v3'
def main():
 # The actual native client fixture body is identical; compare instead of
 # replacing its already qualified source when reusing it with a new core.
 m=runpy.run_path(str(ROOT/'build/check-demand-native.py'));m['main'].__globals__['OUT']=OUT;m['main']()
 m=runpy.run_path(str(ROOT/'build/prepare-demand-transitions.py'));m['main'].__globals__['OUT']=OUT
 import sys
 sys.argv=['prepare-demand-transitions.py','--deterministic'];m['main']()
 source=(ROOT/'build/build-demand-transitions.sh').read_text().replace('build/demand-final-private-v2','build/demand-visible-private-v3')
 source=source.replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."').replace('python3 build/qualify-demand-transitions.py "${1:-}"',"python3 - <<'PY'\nfrom pathlib import Path\nimport runpy,sys\nm=runpy.run_path('build/qualify-demand-transitions.py');m['main'].__globals__['OUT']=Path('build/demand-visible-private-v3').resolve();sys.argv=['qualify','--deterministic'];m['main']()\nPY")
 p=OUT/'build-transitions.sh';p.write_text(source,newline='\n');subprocess.run(['sh',str(p),'--deterministic'],cwd=ROOT,check=True)
if __name__=='__main__':main()
