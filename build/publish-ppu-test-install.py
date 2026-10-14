"""Publish only verified installation receipt, preserving preparation proofs."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
def main():
 source=(ROOT/'build/publish-demand-spells-install.py').read_text()
 source=source.replace('demand-spells','ppu-test')
 source=source.replace("ROOT/'docs/snes-ppu-test-test.txt'","OUT/'TEST-ME.txt'")
 ns={'__file__':str(ROOT/'build/publish-ppu-test-install.py'),'__name__':'ppu_install_receipt'}
 exec(compile(source,'ppu_install_receipt','exec'),ns)
 ns['main'](Path(sys.argv[1]))
if __name__=='__main__':main()
