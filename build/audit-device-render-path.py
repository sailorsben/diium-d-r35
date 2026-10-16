"""Read-only exact-image render/audio/chunk call inventory; no hardware access."""
from pathlib import Path
from hashlib import sha256
import json,re,struct,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'build/lab2-inspection-tools'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
def main():
 path=ROOT/'device-evidence/uart-kernel-offline/kernel.bin';data=path.read_bytes();h=sha256(data).hexdigest();assert h=='21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
 sp=ROOT/'device-evidence/uart-kernel-offline/symbols.txt';symbols=[(int(a,16),n) for a,_,n in re.findall(r'^([0-9a-f]{8}) (.) (.+)$',sp.read_text(),re.M)]
 names={n:i for i,(_,n) in enumerate(symbols)};byaddress={a:n for a,n in symbols};dis=Cs(CS_ARCH_ARM,CS_MODE_ARM);records=[];private=[]
 chosen=['gp_pscaler_open','gp_pscaler_release','gp_pscaler_ioctl','pscaler_wait','pscaler_wait.part.0','pscaler_irq_handler','chunkmem_ioctl','gp_chunk_malloc_ex','snd_pcm_write','snd_pcm_sync_ptr','gpa7xxxa_pcm_new']
 for name in chosen:
  i=names[name];a=symbols[i][0];end=next(x for x,_ in symbols[i+1:] if x>a);block=data[a-0xc0008000:end-0xc0008000];assert len(block)==end-a
  calls=[];decoded=list(dis.disasm(block,a));private.append('\n'+name)
  for v in decoded:
   private.append(f'{v.address:08x} {v.mnemonic} {v.op_str}')
   if v.mnemonic in ('bl','blx') and v.op_str.startswith('#'):
    target=int(v.op_str[1:],0);calls.append({'at':hex(v.address),'target':hex(target),'name':byaddress.get(target,'unknown')})
  records.append({'name':name,'address':hex(a),'bytes':len(block),'sha256':sha256(block).hexdigest(),'direct_calls':calls})
 def sequence(address,n):return [(v.mnemonic,v.op_str) for v in dis.disasm(data[address-0xc0008000:address-0xc0008000+n*4],address)]
 # ioctl table index3 corresponds to 0x80045004 after two subtractions.
 assert sequence(0xc0360b14,3)==[('sub','r3, r1, #0x80000001'),('sub','r3, r3, #0x45000'),('cmp','r3, #0xc')]
 assert struct.unpack_from('<I',data,0xc0360b30+3*4-0xc0008000)[0]==0xc0360bb8
 assert sequence(0xc0360bc4,5)==[('movw','r1, #0x1388'),('cmp','r5, r1'),('mov','r0, r4'),('movlo','r1, r5'),('bl','#0xc035f97c')]
 assert sequence(0xc0360898,1)==[('mov','r5, r2')]
 wait=next(r for r in records if r['name']=='pscaler_wait.part.0');called={c['name'] for c in wait['direct_calls']}
 assert {'__msecs_to_jiffies','init_wait_entry','prepare_to_wait_event','finish_wait','schedule_timeout'}<=called
 out=ROOT/'build/render-pressure-private';out.mkdir(exist_ok=True);(out/'kernel-disassembly.txt').write_text('\n'.join(private)+'\n')
 result={'version':'device-render-path1','kernel_sha256':h,'symbol_table_sha256':sha256(sp.read_bytes()).hexdigest(),'functions':records,
 'verified_contracts':{'scaler_wait_command':'0x80045004','timeout_argument':'scalar unsigned milliseconds clamped to5000 then converted with __msecs_to_jiffies','vendor_argument_3000':'3000ms maximum timeout, not mandatory3000ms delay','completion_wait':'kernel waitqueue / prepare_to_wait_event / schedule_timeout / finish_wait; completion flags are rechecked','new_kernel_or_MMIO_writes':False},
 'configuration_provenance':'build/uart-fix-private/reconstructed.config is a module-build reconstruction, NOT a recovered board configuration; do not promote its HZ/HIGH_RES/PREEMPT choices as device facts.',
 'limits':['Call inventory is not a complete semantic review of every driver.','No persistent-scaler/FIFO/DMA mode is authorized by symbol or queue-field presence.','Stock scaler3000 maximum timeout and measured job cost must remain separate.','Physical timer granularity is measured; exact boot configuration is still not recovered.'],
 'card_access':False,'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}
 (out/'device-path-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['verified_contracts'],indent=2))
if __name__=='__main__':main()
