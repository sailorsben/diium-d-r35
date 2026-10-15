"""Build a persistent card-boot correction from frozen TX1 source; no card access."""
from pathlib import Path
from hashlib import sha256
import importlib.util, json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/uart-fix-private'
def load(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'build'/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def digest(p):return sha256(p.read_bytes()).hexdigest()
def boot_init(original):
 anchor=b'  # D35 SNES MVP: own hardware before the stock supervisor starts.\n'
 assert original.count(anchor)==1 and b'uart-fix1' not in original
 hook=(b'  # Persistent UART TX correction; independent of the one-shot dispatcher.\n'
       b'  if [ -f /usr/retro/uart-fix1/launch.sh ]; then\n'
       b'    /bin/sh /usr/retro/uart-fix1/launch.sh || exit 64\n'
       b'  fi\n')
 return original.replace(anchor,hook+anchor)
def main():
 OUT.mkdir(exist_ok=True)
 src=ROOT/'build/uart-tx-observer.c'
 assert digest(src)=='06b6f0f2d0096a3d0f8ca1c01a584e916c5094f49ce10636119b9e8ef27aaa93'
 text=src.read_text()
 # Only lifetime/cap/description change. All FIFO, bridge, guard and ownership
 # instructions retain the physically tested source. Unsigned stats may wrap;
 # no service decision in this variant depends on a counter.
 changes={'#define CAP 200000u':'#define CAP 0u',
 ' || stats.calls>=CAP':'',
 'Exact-kernel reversible one-byte TX-pending correction test':'Exact-kernel persistent one-byte TX-pending correction'}
 for a,b in changes.items():assert text.count(a)==1;text=text.replace(a,b)
 (OUT/'d35_uart_tx.c').write_text(text,encoding='utf-8',newline='\n')
 p=load('prepare-uart-tx.py');p.OUT=OUT;p.main()
 original=ROOT/'device-evidence/a7-pair-before-20261015T062141Z/retro/init'
 assert digest(original)=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
 (OUT/'init').write_bytes(boot_init(original.read_bytes()))
 (OUT/'preparation.json').write_text(json.dumps({'version':'uart-fix1','base_source_sha256':digest(src),
  'source_transformations':changes,'original_init_sha256':digest(original),'init_sha256':digest(OUT/'init'),
  'lifetime':'until explicit detach or reboot','interrupt_cutoff':False,'firmware_flash_required':False,
  'automatic_every_boot':True,'card_access':False},indent=2)+'\n')
if __name__=='__main__':main()
