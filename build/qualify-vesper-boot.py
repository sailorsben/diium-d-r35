"""Qualify authored boot assets through the owner's exact stock ARM code."""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, json, os, subprocess

ROOT=Path(__file__).resolve().parent.parent

def qualify(stock, output, private):
    spec=importlib.util.spec_from_file_location('boot_art',ROOT/'build/make-vesper-boot.py')
    art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
    art.make(stock,output,private,output/'artwork.png')
    command=(['wsl','sh'] if os.name=='nt' else ['sh'])+['build/check-stock-boot.sh',
             (private/'showlogo-vesper').relative_to(ROOT).as_posix(),
             (output/'ui.raw').relative_to(ROOT).as_posix()]
    result=subprocess.run(command,
                          cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    assert result.returncode==0,result.stdout
    assert result.stdout.startswith('PASS exact stock OpenZipU/UnzipItem decode, 18 ShowSprite frames,')
    (output/'stock-seam-check.log').write_text(result.stdout,encoding='utf-8')
    manifest=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    manifest['stock_loader_and_sprite_check']='passed exact original ARM routines under QEMU; not hardware appearance'
    manifest['verification_sources']={name:sha256((ROOT/name).read_bytes()).hexdigest() for name in
        ('build/make-vesper-boot.py','build/check-stock-boot.c','build/check-stock-boot.sh','build/qualify-vesper-boot.py')}
    manifest['check_sha256']=sha256((output/'stock-seam-check.log').read_bytes()).hexdigest()
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(result.stdout,end='')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'releases/vesper-boot-1')
    p.add_argument('--private-output',type=Path,default=ROOT/'build/vesper-boot-private')
    a=p.parse_args();qualify(a.stock.resolve(),a.output.resolve(),a.private_output.resolve())
