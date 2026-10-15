"""Publish only the verified installation receipt; preserve all preparation proofs."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent

def main(archive):
 code=(ROOT/'build/publish-demand-spells-install.py').read_text().replace('build/demand-spells-private-v1','build/draw-order-test-private-v1').replace('demand-spells','draw-order')
 ns={'__file__':str(Path(__file__).resolve()),'__name__':'draw_order_install_receipt'}
 exec(compile(code,'draw_order_install_receipt','exec'),ns);ns['main'](archive)
if __name__=='__main__':main(Path(sys.argv[1]))
