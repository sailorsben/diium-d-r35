"""Same raw original-command qualification, plus the new disjoint work census."""
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent.parent
def main():
 m=runpy.run_path(str(ROOT/'build/qualify-demand-final.py'))
 g=m['main'].__globals__;g['OUT']=ROOT/'build/demand-visible-private-v3'
 g['FIELDS']+=['coverage_probes','covered_clips','clip_cells_eliminated','clip_tile_rows_eliminated','clip_depth_vectors','clip_depth_scalar_reads','coverage_misses','coverage_vetoes']
 m['main']()
if __name__=='__main__':main()
