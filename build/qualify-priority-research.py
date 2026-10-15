"""Positive-path priority hypothesis across all18 contexts; no timing claims."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def main():
 code=(ROOT/'build/qualify-current-work-census.py').read_text()
 code=code.replace("ROOT/'build/current-work-private-v1'","ROOT/'build/priority-research-private-v1'")
 code=code.replace("selected=[c for c in cases if c['seq'] in (0,1,8,12,16,17)]","selected=cases")
 code=code.replace("'raw_graphics_PCM_geometry_calls':7200","'raw_graphics_PCM_geometry_calls':21600")
 ns={'__file__':str(Path(__file__).resolve()),'__name__':'priority_qualification'}
 exec(compile(code,'priority_qualification','exec'),ns)
 ns['FIELDS'].update({57:'top_priority_passes',58:'priority_filtered_tiles'})
 ns['main']()
if __name__=='__main__':main()
