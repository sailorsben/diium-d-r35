"""Fresh native client and resolution/state seams; all qualified trees retained."""
from pathlib import Path
import runpy,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ppu-refinements-private-v4/integration'
def main():
 assert not OUT.exists();OUT.mkdir()
 variant='rows-v2' if '--rows' in sys.argv else 'combined'
 shutil.copytree(ROOT/'build/ppu-refinements-private-v4'/variant,OUT/'core',ignore=shutil.ignore_patterns('*.o'))
 shutil.copy2(ROOT/'build/ppu-refinements-private-v4/compare.c',OUT/'compare.c')
 shutil.copy2(ROOT/'build/ppu-refinements-private-v4/demand-equivalence.c',OUT/'demand-equivalence.c')
 m=runpy.run_path(str(ROOT/'build/check-demand-native.py'));m['main'].__globals__['OUT']=OUT;m['main']()
 # The reference and candidate receive the previously documented test-only
 # HDMA pointer initialization, never an emulated-field mask or shipped patch.
 code=(ROOT/'build/prepare-demand-transitions.py').read_text().replace("ROOT/'build/common-band-private-v3/core'","ROOT/'build/demand-visible-private-v3/core'")
 ns={'__file__':str(ROOT/'build/prepare-demand-transitions.py'),'__name__':'ppu_transitions'};exec(compile(code,'ppu_transitions','exec'),ns)
 ns['OUT']=OUT;sys.argv=['prepare','--deterministic'];ns['main']()
 relative=OUT.relative_to(ROOT).as_posix()
 source=(ROOT/'build/build-demand-transitions.sh').read_text().replace('build/demand-final-private-v2',relative)
 source=source.replace('"$(dirname "$0")/.."','"$(dirname "$0")/../../.."').replace('-L../../sysroot/lib','-L../../../sysroot/lib')
 source=source.replace('python3 build/qualify-demand-transitions.py "${1:-}"',"python3 - <<'PY'\nfrom pathlib import Path\nimport runpy,sys\nm=runpy.run_path('build/qualify-demand-transitions.py');m['main'].__globals__['OUT']=Path('"+relative+"').resolve();sys.argv=['qualify','--deterministic'];m['main']()\nPY")
 script=OUT/'build-transitions.sh';script.write_text(source,newline='\n');subprocess.run(['sh',str(script),'--deterministic'],check=True)
if __name__=='__main__':
 if '--rows' in sys.argv:OUT=ROOT/'build/ppu-refinements-private-v4/row-integration'
 main()
