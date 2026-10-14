"""Extract the actual direct-copy branch; compare a two-span algorithm offline."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/architecture-audit-private-v1'
def main():
 source=ROOT/'build/common-band-private-v3/core/source/apu_blargg.c';s=source.read_text();a=s.index('\tif (r_step == 65536)',s.index('static void resampler_read('));b=s.index('   i_position = rb_start >> 1;',a)
 original=s[a:b]
 wrapper='''#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static unsigned char ring[65536],*rb_buffer=ring;
static int rb_buffer_size,rb_start,rb_size,r_step=65536;
static unsigned copies;
static void *copy_count(void *d,const void *s,size_t n){copies++;return memcpy(d,s,n);}
#define memcpy copy_count
static void old_read(int16_t *data,int32_t num_samples){
'''+original+'''assert(0);}
static void new_read(int16_t *data,int32_t num_samples){
 while(num_samples>0){int bytes=num_samples*2,tail=rb_buffer_size-rb_start;if(bytes>tail)bytes=tail;
 memcpy(data,rb_buffer+rb_start,bytes);data+=bytes/2;rb_start+=bytes;rb_size-=bytes;num_samples-=bytes/2;
 if(rb_start==rb_buffer_size)rb_start=0;}
}
static unsigned long cases;
static unsigned saved_old,saved_new;
static void check(int capacity,int start,int samples){
 int16_t a[32768],b[32768];memset(a,0x5a,sizeof(a));memset(b,0x5a,sizeof(b));
 for(int i=0;i<capacity;i++)ring[i]=(unsigned char)(i*31+i/256);
 rb_buffer_size=capacity;rb_start=start;rb_size=capacity;copies=0;old_read(a,samples);
 int end=rb_start,size=rb_size;unsigned old=copies;
 rb_start=start;rb_size=capacity;copies=0;new_read(b,samples);
 assert(rb_start==end&&rb_size==size&&!memcmp(a,b,sizeof(a))&&copies<=2);
 if(capacity==32768&&start==32764&&samples==1024){saved_old=old;saved_new=copies;}
 cases++;
}
int main(void){
 for(int c=4;c<=256;c+=4)for(int start=0;start<c;start+=4)for(int n=0;n<=c/2;n+=2)check(c,start,n);
 for(int start=0;start<32768;start+=4)for(int n=0;n<=2048;n+=128)check(32768,start,n);
 check(32768,32764,1024);assert(saved_old==512&&saved_new==2);
 printf("PASS %lu exact ring states; synthetic tail4/sample1024 memcpy calls %u -> %u; no timing evidence\\n",cases,saved_old,saved_new);
}
'''
 (OUT/'ring-check.c').write_text(wrapper,newline='\n')
 subprocess.run(['gcc','-O2','-std=c99','-Wall','-Wextra','-Werror',str(OUT/'ring-check.c'),'-o',str(OUT/'ring-check')],check=True)
 r=subprocess.run([str(OUT/'ring-check')],check=True,capture_output=True,text=True)
 (OUT/'ring-check.log').write_text(r.stdout)
 (OUT/'ring-proof.json').write_text(json.dumps({'passed':True,'actual_branch_source_sha256':sha256(source.read_bytes()).hexdigest(),'exact_test_output':r.stdout.strip(),'synthetic_worst_example':{'copy_calls_before':512,'copy_calls_after':2},'A7_timing':False,'production_candidate_implemented':False,'limits':['Focused direct-copy equivalence only, not a complete core optimization.','Occurrence and savings must come from workload evidence, never the synthetic worst case.']},indent=2)+'\n')
 print(r.stdout,end='')
if __name__=='__main__':main()
