"""Save an exact read-only Windows CHKDSK report; never repair/arm the card."""
from pathlib import Path
import argparse, subprocess
ROOT=Path(__file__).resolve().parent.parent
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();output=a.output.resolve();assert output.is_relative_to(ROOT/'device-evidence')
    assert not output.exists()
    result=subprocess.run(['chkdsk','D:'],input=b'N\r\n',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output.write_text(result.stdout.decode('cp437').replace('\r\n','\n'),encoding='utf-8')
    print(result.stdout.decode('cp437'));print('Read-only CHKDSK exit:',result.returncode)
