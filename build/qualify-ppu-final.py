"""Qualify only changed final PPU combination; do not repeat isolated variants."""
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent.parent
def main():
 m=runpy.run_path(str(ROOT/'build/qualify-ppu-refinements.py'));g=m['main'].__globals__
 g['OUT']=ROOT/'build/ppu-refinements-private-v5';g['LABELS']=('combined','combined-counted');m['main']()
if __name__=='__main__':main()
