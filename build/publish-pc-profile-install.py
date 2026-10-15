"""Publish the verified PC diagnostic installation, preserving preparation proofs."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent

def main(archive):
 source=(ROOT/'build/publish-demand-spells-install.py').read_text()
 source=source.replace('build/demand-spells-private-v1','build/current-pc-profile-private-v1').replace('demand-spells','pc-profile')
 target=ROOT/'evidence/2026-10-14/pc-profile'
 target.mkdir(parents=True,exist_ok=False)
 ns={'__file__':str(Path(__file__).resolve()),'__name__':'pc_profile_install_receipt'}
 exec(compile(source,'pc_profile_install_receipt','exec'),ns)
 ns['main'](archive)
if __name__=='__main__':main(Path(sys.argv[1]))
