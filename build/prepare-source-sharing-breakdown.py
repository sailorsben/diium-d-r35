"""Split source matches by BG/OBJ in a separate existing observer clone."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/source-sharing-private-v1'
OLD=ROOT/'build/architecture-stream-private-v1'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists();OUT.mkdir();shutil.copytree(OLD/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'));core=OUT/'core'
 for name in ('source/a7_arch_audit.h','source/a7_arch_stream.h','libretro.c'):
  p=core/name;s=p.read_text(encoding='utf-8');assert 'd35_arch[96]' in s;write(p,s.replace('d35_arch[96]','d35_arch[112]'))
 p=core/'source/a7_arch_stream.h';s=p.read_text(encoding='utf-8').replace('arch_bg>=4','arch_bg>=5')
 s=s.replace(' d35_arch[sub?75:76]++;',' if(arch_bg<4)d35_arch[sub?75:76]++;\n d35_arch[96+arch_bg*3+(sub?0:1)]++;')
 # Identity includes every source key, retaining overlapping OBJ producers
 # instead of overwriting the earlier producer solely by destination.
 s=s.replace('s->bg==arch_bg&&s->offset==(unsigned)offset','s->bg==arch_bg&&s->offset==(unsigned)offset&&s->source==source&&s->palette==palette&&s->flip==flip')
 s=s.replace('else if(s->source==source&&s->palette==palette&&s->flip==flip)d35_arch[77]++;','else {if(arch_bg<4)d35_arch[77]++;d35_arch[98+arch_bg*3]++;}')
 write(p,s)
 s=(OLD/'compare.c').read_text(encoding='utf-8').replace('ac[96]','ac[112]').replace('j<96','j<112');write(OUT/'compare.c',s)
 shutil.copy2(OLD/'inputs.json',OUT/'inputs.json')
 print('Prepared exact source-key set, BG0/1/2/3 and full-tile OBJ populations')
if __name__=='__main__':main()
