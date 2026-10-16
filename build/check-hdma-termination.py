"""Exercise extracted full HDMA function against logical transfer-address contracts."""
from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-fixes-private-v1'
PRE='''#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
#define ONE_CYCLE 6
#define SLOW_ONE_CYCLE 8
typedef struct {unsigned LineCount,FirstLine,ABank,BAddress,Repeat,HDMAIndirectAddressing,IndirectBank,TransferMode;uint16_t Address,IndirectAddress;} SDMA;
static SDMA DMA[8];static struct {int InDMA,Cycles;}CPU;
static struct {uint8_t FillRAM[32768];} Memory;
static uint8_t ram[65552],*HDMAMemPointers[8],*HDMABasePointers[8];
static int HDMA_ModeByteCounts[8]={1,2,2,4,4,4,2,4};static unsigned writes;
static uint8_t S9xGetByte(unsigned a){return ram[a&65535];}
static uint16_t S9xGetWord(unsigned a){return S9xGetByte(a)|(S9xGetByte(a+1)<<8);}
static uint8_t *S9xGetMemPointer(unsigned a){return ram+(a&65535);}
static void S9xSetPPU(uint8_t v,unsigned a){(void)v;(void)a;writes++;}
'''
POST='''int main(void){unsigned cases=0,failures=0;
for(unsigned channel=0;channel<8;channel++)for(unsigned mode=0;mode<8;mode++)for(unsigned indirect=0;indirect<2;indirect++){
 memset(DMA,0,sizeof(DMA));memset(ram,0,sizeof(ram));memset(&Memory,0,sizeof(Memory));memset(HDMAMemPointers,0,sizeof(HDMAMemPointers));memset(HDMABasePointers,0,sizeof(HDMABasePointers));writes=0;
 SDMA *p=DMA+channel;p->Address=0x100;p->TransferMode=mode;p->BAddress=0x22;p->HDMAIndirectAddressing=indirect;ram[0x100]=0x81;ram[0x101]=0x00;ram[0x102]=0x02;
 if(!indirect)ram[0x101+HDMA_ModeByteCounts[mode]]=0;
 assert(S9xDoHDMA(1u<<channel)==(1u<<channel));unsigned expected=(indirect?0x200:0x101)+HDMA_ModeByteCounts[mode];assert(p->IndirectAddress==expected&&writes==(unsigned)HDMA_ModeByteCounts[mode]);
 assert(S9xDoHDMA(1u<<channel)==0);unsigned shadow=Memory.FillRAM[0x4305+(channel<<4)]|(Memory.FillRAM[0x4306+(channel<<4)]<<8);if(shadow!=expected||p->IndirectAddress!=expected)failures++;assert(!CPU.InDMA);cases++;
}
for(unsigned channel=0;channel<8;channel++)for(unsigned stale=1;stale<5;stale++){
 memset(DMA,0,sizeof(DMA));memset(ram,0,sizeof(ram));DMA[channel].Address=0x100;DMA[channel].IndirectAddress=0x7654;HDMAMemPointers[channel]=NULL;HDMABasePointers[channel]=ram+stale*13;
 assert(S9xDoHDMA(1u<<channel)==0);unsigned shadow=Memory.FillRAM[0x4305+(channel<<4)]|(Memory.FillRAM[0x4306+(channel<<4)]<<8);if(shadow!=0x7654)failures++;cases++;
}
printf("cases=%u failures=%u\\n",cases,failures);return failures?1:0;}
'''
def main():
 results=[]
 for label,source in [('old',ROOT/'build/demand-visible-private-v3/core/source/dma.c'),('fixed',OUT/'core/source/dma.c')]:
  s=source.read_text(encoding='utf-8');part=s[s.index('uint8_t S9xDoHDMA('):s.index('void S9xResetDMA(')]
  c=OUT/f'hdma-{label}.c';c.write_text(PRE+part+POST);binary=OUT/f'hdma-{label}'
  subprocess.run(['gcc','-std=c99','-O2','-Wall','-Wextra','-Werror',str(c),'-o',str(binary)],check=True)
  r=subprocess.run([str(binary)],capture_output=True,text=True);assert r.returncode==(1 if label=='old' else 0),(label,r.stdout,r.stderr)
  results.append({'source':str(source.relative_to(ROOT)),'label':label,'returncode':r.returncode,'output':r.stdout.strip()});print(label,r.stdout.strip(),flush=True)
 (OUT/'hdma-check.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
