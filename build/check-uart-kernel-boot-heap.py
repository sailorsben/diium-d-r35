"""Additional exact head.S 64-KiB decompressor heap check; no card access."""
from pathlib import Path
from hashlib import sha256
import json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/uart-kernel-firmware1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 q=json.loads((OUT/'qualification.json').read_text());src=ROOT/'build/check-kernel-decompressor.c';assert digest(src)==q['sources']['build/check-kernel-decompressor.c']
 text=src.read_text();assert text.count('(0x02000000,0x03000000,0x03200000,0)')==1
 helper=ROOT/'build/uart-kernel-check/heap64k.c';helper.write_bytes(text.replace('(0x02000000,0x03000000,0x03200000,0)','(0x02000000,0x03000000,0x03010000,0)').encode())
 prefix=['wsl','--exec'] if os.name=='nt' else []
 def run(args):
  p=subprocess.run(prefix+args,cwd=ROOT,capture_output=True,timeout=60);assert p.returncode==0,(p.returncode,p.stderr.decode());return p.stdout.decode()
 run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-marm','-O2','-Wall','-Wextra','-Werror','-fno-delete-null-pointer-checks','-no-pie','-Wl,-Ttext-segment=0x10000000','build/uart-kernel-check/heap64k.c','-o','build/uart-kernel-check/heap64k'])
 results={}
 for label,z,k in [('baseline','build/uart-kernel-check/baseline.zImage','device-evidence/uart-kernel-offline/kernel.bin'),('corrected','device-evidence/uart-kernel-firmware1/zImage.bin','device-evidence/uart-kernel-firmware1/kernel.bin')]:
  results[label]=run(['qemu-arm','-cpu','cortex-a7','-B','0x40000000','-L','/usr/arm-linux-gnueabihf','build/uart-kernel-check/heap64k',z,k]);assert results[label].startswith('PASS ')
 report={'passed':True,'heap_bytes':65536,'baseline_and_candidate_full_output_equal':True,'original_source_sha256':digest(src),'probe_source_sha256':digest(Path(__file__)),'generated_fixture_sha256':digest(helper),'zImage_sha256':digest(OUT/'zImage.bin'),'stdout':results,'device_access':False,'kernel_boot_executed':False}
 (OUT/'boot-heap-qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
