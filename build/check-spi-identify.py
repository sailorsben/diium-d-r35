"""Qualify fixed SPI read packets, refusal cases, actual ARM and owned timeout.

Fake kernel responses exercise the recovered interface without hardware access.
"""
from pathlib import Path
from hashlib import sha256
import json,re,shutil,subprocess,tempfile,time
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/spi-identify-out'
def linux(p):
    p=Path(p).resolve();return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def wsl(args,**kw):return subprocess.run(['wsl','--exec',*map(str,args)],check=True,**kw)

def run():
    wsl(['sh',linux(ROOT/'build/build-spi-identify.sh')])
    checks=[]
    with tempfile.TemporaryDirectory(prefix='spi-check-',dir=OUT) as name:
        t=Path(name);h=t/'harness.c'
        h.write_text(r'''
#define ioctl kernel_fixture_ioctl
#define opendir fixture_opendir
#define main device_main
#include "spi-identify.c"
#undef main
#undef ioctl
#undef opendir
#include <stdarg.h>
#include <assert.h>
extern DIR *opendir(const char *);
static unsigned sample,setting_reads,case_id;
DIR *fixture_opendir(const char *path) {
 if(case_id==14&&ends_fixture(path,"/proc")) { struct timespec t={5,0};syscall(SYS_nanosleep,&t,NULL); }
 return opendir(path);
}
int kernel_fixture_ioctl(int fd,unsigned long request,...) {
 (void)fd;va_list args;va_start(args,request);void *value=va_arg(args,void *);va_end(args);
 if(request==SPI_IOC_RD_MODE32) { *(uint32_t*)value=case_id==9?1:case_id==11?SPI_NO_CS:SPI_RX_DUAL;return 0; }
 if(request==SPI_IOC_RD_BITS_PER_WORD) { *(unsigned char*)value=case_id==12?16:8;return 0; }
 if(request==SPI_IOC_RD_MAX_SPEED_HZ) { *(uint32_t*)value=case_id==13?0:case_id==10&&setting_reads++?19000000:20000000;return 0; }
 assert(request==0x40406b00ul);struct spi_ioc_transfer *x=value;
 assert(x[0].tx_buf&&x[0].rx_buf==0&&x[0].len==1&&x[0].speed_hz==1000000&&x[0].bits_per_word==8);
 assert(x[0].tx_nbits==1&&x[0].rx_nbits==0&&x[0].cs_change==0&&x[0].delay_usecs==0&&x[0].pad==0);
 assert(x[1].tx_buf==0&&x[1].rx_buf&&x[1].speed_hz==1000000&&x[1].bits_per_word==8);
 assert(x[1].rx_nbits==1&&x[1].tx_nbits==0&&x[1].cs_change==0&&x[1].delay_usecs==0&&x[1].pad==0);
 unsigned char command=*(unsigned char*)(uintptr_t)x[0].tx_buf,*out=(void*)(uintptr_t)x[1].rx_buf;
 assert((command==5&&x[1].len==1)||(command==0x9f&&x[1].len==6));
 if(case_id==8) { errno=EINVAL;return -1; }
 if(case_id==7)return 1;
 if(command==5)out[0]=case_id==3?1:0;
 else {
  const unsigned char id[6]={0xef,0x40,0x17,0,0,0};sample++;
  if(case_id!=5)memcpy(out,id,6);
  if(case_id==2)memset(out,0,6);
  if(case_id==4)memset(out,0xff,6);
  if(case_id==6&&sample==2)out[2]^=1;
 }
 return (int)(x[0].len+x[1].len);
}
int main(int argc,char **argv) {
 assert(argc==2||argc==4);case_id=pid_number(argv[1]);
 if(argc==4) { char *args[]={argv[0],argv[2],argv[3]};return device_main(3,args); }
 Result r={0};int error=identify(77,&r);
 const int expected[]={0,0,ENODATA,EBUSY,ENODATA,ENODATA,EILSEQ,EIO,EINVAL,EPERM,ESTALE,EPERM,EPERM,EPERM};
 assert(case_id<14&&error==expected[case_id]);
 if(case_id==1)assert(r.operations==5&&!memcmp(r.id[0],r.id[2],6));
 if(case_id==3)assert(r.operations==1&&sample==0);
 if(case_id==9||case_id>=11)assert(r.operations==0);
 unsigned char data[6];assert(exchange(77,6,data,1,1000000,&r)==EPERM);
 puts("fixed read contract passed");return 0;
}
'''.replace('#define ioctl kernel_fixture_ioctl','#define ends_fixture(p,s) (strlen(p)>=strlen(s)&&!strcmp((p)+strlen(p)-strlen(s),(s)))\n#define ioctl kernel_fixture_ioctl'),encoding='utf-8',newline='\n')
        common=['-std=gnu99','-O2','-Wall','-Wextra','-Werror','-Wno-format-truncation','-I'+linux(ROOT/'build')]
        wsl(['gcc',*common,linux(h),'-o',linux(t/'native')])
        wsl(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm',
             '-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32',
             *common,'-no-pie','-nostdlib','/usr/arm-linux-gnueabihf/lib/crt1.o',linux(h),
             '-L'+linux(ROOT/'build/sysroot/lib'),'-Wl,--no-as-needed','-l:libc-2.30.so','-l:libgcc_s.so.1','-l:ld-2.30.so','-o',linux(t/'arm')])
        for label,exe in [('native',[linux(t/'native')]),('arm',['qemu-arm','-cpu','cortex-a7','-L',linux(ROOT/'build/sysroot'),linux(t/'arm')])]:
            for n in range(1,14):wsl(exe+[str(n)],stdout=subprocess.DEVNULL)
            checks.append(label+': fixed 05/9f two-transfer ABI; stable repeated ID; busy/empty/floating/unchanged/inconsistent/short/error/config-change refusals; write-enable denied')
            fixture=t/(label+'-root');(fixture/'proc').mkdir(parents=True);(fixture/'dev').mkdir()
            (fixture/'dev/spidev0.0').write_bytes(b'ordinary file must never receive ioctl')
            result=t/(label+'-wrong-node')
            p=subprocess.run(['wsl','--exec',*exe,'1',linux(fixture),linux(result)],stdout=subprocess.PIPE)
            data=json.loads((result/'result.json').read_text());assert p.returncode==1 and data['errno']==1 and data['operations']==0
            checks.append(label+': real supervisor refuses wrong device type before open/transactions')
            (fixture/'proc/44/fd').mkdir(parents=True);wsl(['ln','-s','/dev/spidev0.0',linux(fixture/'proc/44/fd/8')])
            result=t/(label+'-owner');p=subprocess.run(['wsl','--exec',*exe,'1',linux(fixture),linux(result)],stdout=subprocess.PIPE)
            data=json.loads((result/'result.json').read_text());assert p.returncode==1 and data['errno']==16 and data['owner_pid']==44 and data['operations']==0
            checks.append(label+': active owner refuses transactions without killing it')
            result=t/(label+'-timeout');begin=time.monotonic()
            p=subprocess.run(['wsl','--exec',*exe,'14',linux(fixture),linux(result)],stdout=subprocess.PIPE)
            data=json.loads((result/'result.json').read_text());assert p.returncode==1 and data['timed_out'] and not data['reap_pending'] and time.monotonic()-begin<5
            checks.append(label+': actual owned-child deadline, SIGKILL and reap')
        # Execute the release ARM binary (without fixtures) on the wrong node.
        result=t/'actual-arm-refusal'
        p=subprocess.run(['wsl','--exec','qemu-arm','-cpu','cortex-a7','-L',linux(ROOT/'build/sysroot'),linux(OUT/'spi-identify'),linux(t/'native-root'),linux(result)])
        data=json.loads((result/'result.json').read_text());assert p.returncode==1 and data['operations']==0
        checks.append('exact release ARM binary rejects pre-existing SPI owner without hardware access')
        busybox=ROOT/'device-evidence/snes-mvp-return-20261009T165057Z/vesper-boot-probe/results/busybox'
        base=t/'wrapper';base.mkdir();(base/'armed').write_text('independent-id\n')
        (base/'spi-identify').write_text('#!/bin/sh\nprintf read-only-fixture\n',encoding='utf-8',newline='\n')
        wsl(['chmod','+x',linux(base/'spi-identify')]);tools=t/'tools';tools.mkdir()
        for n in ['mv','sync']:wsl(['ln','-s','/bin/'+n,linux(tools/n)])
        call=['env','PATH='+linux(tools),'D35_SPI_BASE='+linux(base),'D35_SPI_ROOT='+linux(t/'native-root'),
              '/usr/bin/qemu-arm','-cpu','cortex-a7','-L',linux(ROOT/'build/sysroot'),linux(busybox),'sh',linux(ROOT/'build/launch-spi-identify.sh')]
        wsl(call);assert not (base/'armed').exists() and (base/'consumed').read_text()=='independent-id\n'
        before=(base/'startup.log').read_bytes();wsl(call);assert (base/'startup.log').read_bytes()==before
        checks.append('actual firmware BusyBox consume-first synchronous wrapper; next boot no-op')
    abi=(OUT/'abi.txt').read_text();versions=re.findall(r'Name: GLIBC_([0-9.]+)',abi)
    assert versions and all(tuple(map(int,v.split('.')))<=(2,30) for v in versions)
    checks.append('exact ARM GLIBC dependencies <= 2.30')
    release=ROOT/'releases/spi-identify-1';release.mkdir(exist_ok=True)
    qualification={'software_checks_passed':True,'checks':checks,'physical_execution':'pending'}
    (OUT/'qualification.json').write_text(json.dumps(qualification,indent=2)+'\n',encoding='utf-8',newline='\n')
    for p,n in [(OUT/'spi-identify','spi-identify'),(OUT/'abi.txt','abi.txt'),(OUT/'qualification.json','qualification.json'),(ROOT/'build/launch-spi-identify.sh','launch.sh')]:shutil.copyfile(p,release/n)
    names=['build/spi-identify.c','build/build-spi-identify.sh','build/launch-spi-identify.sh','build/check-spi-identify.py','build/manage-spi-identify.py']
    manifest={'version':1,'physical_execution':'pending','software_checks_passed':True,'fixed_commands':['05','9f'],
        'flash_writes':False,'global_config_writes':False,'source_hashes':{n:sha256((ROOT/n).read_bytes()).hexdigest() for n in names},
        'release_hashes':{n:sha256((release/n).read_bytes()).hexdigest() for n in ['spi-identify','abi.txt','qualification.json','launch.sh']}}
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'passed_checks':len(checks),'physical_execution':'pending','release':str(release)},indent=2))
if __name__=='__main__':run()
