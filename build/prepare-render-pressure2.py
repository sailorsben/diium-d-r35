"""Freeze physically used board/audio support and prepare a ROM-free lab."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/render-pressure2-private'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not OUT.exists(),'Preserve existing experiments; use a fresh version'
 old=ROOT/'build/draw-order-test-private-v1';q=json.loads((old/'verification.json').read_text())
 OUT.mkdir();(OUT/'runner').mkdir()
 names=['board.c','board.h','audio-owner.c','audio-pipe.h','native-pcm.c','native-pcm.h','startup.c','startup.h','platform.c','platform.h','timing.c','timing.h']
 for n in names:
  p=old/'runner'/n;key=p.relative_to(ROOT).as_posix();assert digest(p)==q['source_hashes'][key],key;shutil.copyfile(p,OUT/'runner'/n)
 wrapper=(ROOT/'build/launch-platform-lab2.sh').read_text().replace('/usr/retro/platform-lab','/usr/retro/render-pressure2').replace('lab2 wrapper_pid','render-pressure2 wrapper_pid').replace('"$LAB/platform-lab"','"$LAB/render-pressure"')
 check='''uart_check() {
  IFS= read -r UART < "$PROC/d35_uart_tx" || return 1
  printf '%s\\n' "$UART" > "$OUT/uart-$1.txt"
  case "$UART" in 'version=4 result=0 irq=19 attached=1 '*fault=0\\ bypass=0\\ *cap=0) return 0;; *) return 1;; esac
}
uart_check before || exit 1
'''
 wrapper=wrapper.replace('STOP=${D35_LAB_SPLASH_STOP',check+'STOP=${D35_LAB_SPLASH_STOP').replace('RESULT=$?\n','RESULT=$?\ncase "$RESULT" in 0|1|5) ;; *) RESULT=72;; esac\nif ! uart_check after; then [ "$RESULT" -eq 72 ] || RESULT=1; fi\n')
 (OUT/'launch.sh').write_text(wrapper,encoding='utf-8',newline='\n')
 (OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /bin/sh /usr/retro/render-pressure2/launch.sh\n',encoding='utf-8',newline='\n')
 report={'version':'render-pressure2','ROM_required':False,'phases':70,'copied_support':{n:digest(OUT/'runner'/n) for n in names},
 'frozen_suite_verification_sha256':digest(old/'verification.json'),'card_access':False,'physical_result':'PENDING','installed':False,'armed':False,
 'qualification_boundary':'Copied board/audio semantics are physically exercised; new controller and synthetic workloads require their own device return.'}
 (OUT/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
