"""Actual native/state/resolution checks for the final inlined combination."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def main():
 source=(ROOT/'build/check-ppu-integration.py').read_text().replace('ppu-refinements-private-v4','ppu-refinements-private-v5')
 ns={'__file__':str(ROOT/'build/check-ppu-integration.py'),'__name__':'ppu_final_integration'}
 exec(compile(source,'ppu_final_integration','exec'),ns);ns['main']()
if __name__=='__main__':main()
