/* Execute exact stock xintiao against independent ADC/GPIO fixtures. RAM only. */
#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <elf.h>
#include <stdint.h>
#include <setjmp.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
static unsigned raw,read_calls,open_calls,gpio_a,gpio_b;static int read_error,start_error,open_error;
static jmp_buf shutdown_boundary;static unsigned warning_steps;
static FILE *config_open(const char *path,const char *mode){
 static char config[]="318,310,300,290,275\r\n";
 printf("Config open: %s mode=%s\n",path,mode);fflush(stdout);
 assert(!strcmp(path,"/usr/retro/adcset.ini")&&!strcmp(mode,"r+b"));
 return fmemopen(config,sizeof(config)-1,"r");
}
static const char *workpath(void){return "/usr/retro/";}
static int warning_data(void *buffer,const char *path,const char *entry){
 assert(buffer);printf("Warning asset: %s entry=%s\n",path,entry);warning_steps|=1;return 0;
}
static int display(void *buffer,int w,int h,int stride){assert(buffer&&w==640&&h==480&&stride==1280);warning_steps|=2;return 0;}
static unsigned delay(unsigned seconds){assert(seconds==5);warning_steps|=4;return 0;}
static int backlight(int value){assert(value==0);warning_steps|=8;return 0;}
static int release(void *buffer){free(buffer);return 0;}
static int shutdown_request(const char *command){
 printf("Intercepted stock shutdown command: %s\n",command);
 assert(!strcmp(command,"poweroff"));warning_steps|=16;longjmp(shutdown_boundary,1);
}
static void forbidden(void){fputs("Unexpected stock import\n",stderr);abort();}
static int quiet(const char *s,...){(void)s;return 0;}
static int adc_open(const char *p,int flags,...){assert(!strcmp(p,"/dev/adc")&&flags==0);open_calls++;return open_error?-1:707;}
static int adc_close(int fd){assert(fd==(open_error?-1:707));return 0;}
static int adc_ioctl(int fd,unsigned request,uintptr_t arg){assert(fd==(open_error?-1:707)&&request==0x40044701&&arg==2);return start_error?-1:0;}
static ssize_t adc_read(int fd,void *p,size_t count){assert(fd==(open_error?-1:707)&&count==4);read_calls++;if(read_error)return -1;uint16_t v=(uint16_t)raw;memcpy(p,&v,2);return 2;}
static int gpio(unsigned pin){assert(pin==0x20b||pin==0x20e);return pin==0x20b?(int)gpio_a:(int)gpio_b;}
static int refresh(int value){assert(value==1);return 0;}
static void patch(uint32_t address,void *callback)
{
    uint32_t instruction=0xe51ff004; /* ARM ldr pc,[pc,#-4], preserving all arguments */
    memcpy((void *)(uintptr_t)address,&instruction,4);
    uint32_t pointer=(uint32_t)(uintptr_t)callback;
    memcpy((void *)(uintptr_t)(address+4),&pointer,4);
    __builtin___clear_cache((void *)(uintptr_t)address,(void *)(uintptr_t)(address+8));
}
static uint8_t *read_all(const char *path,size_t *size)
{
    FILE *f=fopen(path,"rb");assert(f && !fseek(f,0,SEEK_END));
    long n=ftell(f);assert(n>0);rewind(f);uint8_t *data=malloc((size_t)n);
    assert(data && fread(data,1,(size_t)n,f)==(size_t)n && !fclose(f));*size=(size_t)n;return data;
}
static uintptr_t symbol(const uint8_t *file,const char *name)
{
    const Elf32_Ehdr *h=(const void *)file;const Elf32_Shdr *s=(const void *)(file+h->e_shoff);
    for(unsigned i=0;i<h->e_shnum;i++)if(s[i].sh_type==SHT_SYMTAB){
        const Elf32_Sym *symbols=(const void *)(file+s[i].sh_offset);
        const char *strings=(const void *)(file+s[s[i].sh_link].sh_offset);
        for(unsigned j=0;j<s[i].sh_size/sizeof(*symbols);j++)
            if(!strcmp(strings+symbols[j].st_name,name))return symbols[j].st_value;
    }
    forbidden();return 0;
}
static void *import(const char *n){
 if(!strcmp(n,"__gmon_start__"))return NULL;
 if(!strcmp(n,"open"))return adc_open;if(!strcmp(n,"close"))return adc_close;if(!strcmp(n,"read"))return adc_read;if(!strcmp(n,"ioctl"))return adc_ioctl;
 if(!strcmp(n,"printf")||!strcmp(n,"puts"))return quiet;
 if(!strcmp(n,"stderr"))return &stderr;
 if(!strcmp(n,"fopen"))return config_open;if(!strcmp(n,"fclose"))return fclose;
 if(!strcmp(n,"__isoc99_fscanf"))return fscanf;if(!strcmp(n,"sprintf"))return sprintf;
 if(!strcmp(n,"malloc"))return malloc;if(!strcmp(n,"sleep"))return delay;if(!strcmp(n,"system"))return shutdown_request;
 return forbidden;
}
static int reference(unsigned value,int previous,const int *t){
 int level;
 if(value>(unsigned)t[0]){level=0;if(previous==1&&value<=(unsigned)(t[0]+2))level=1;}
 else if(value>(unsigned)t[1]){level=1;if(previous==0&&value>=(unsigned)(t[0]-2))level=0;if(previous==2&&value<=(unsigned)(t[1]+2))level=2;}
 else if(value>(unsigned)t[2]){level=2;if(previous==1&&value>=(unsigned)(t[1]-2))level=1;if(previous==3&&value<=(unsigned)(t[2]+1))level=3;}
 else if(value>(unsigned)t[3]){level=3;if(previous==2&&value>=(unsigned)(t[2]-1))level=2;if(previous==4&&value<=(unsigned)(t[3]+1))level=4;}
 else if(value>(unsigned)t[4]){level=4;if(previous==3&&value>=(unsigned)t[3])level=3;}
 else level=-1;
 if(gpio_a&&gpio_b)level=5;return level;
}
int main(int argc,char **argv){assert(argc==2);size_t size;uint8_t *file=read_all(argv[1],&size);
    const Elf32_Ehdr *h=(const void *)file;
    assert(size==1660140 && !memcmp(h->e_ident,ELFMAG,4) && h->e_machine==EM_ARM && h->e_type==ET_EXEC);
    void *mapped=mmap((void *)0x10000,0x200000,PROT_READ|PROT_WRITE|PROT_EXEC,
                     MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(mapped==(void *)0x10000);
    const Elf32_Phdr *ph=(const void *)(file+h->e_phoff);
    for(unsigned i=0;i<h->e_phnum;i++)if(ph[i].p_type==PT_LOAD){
        assert(ph[i].p_vaddr>=0x10000 && ph[i].p_vaddr+ph[i].p_memsz<=0x210000);
        assert(ph[i].p_offset+ph[i].p_filesz<=size);
        memcpy((void *)(uintptr_t)ph[i].p_vaddr,file+ph[i].p_offset,ph[i].p_filesz);
    }
    const Elf32_Shdr *sh=(const void *)(file+h->e_shoff);
    for(unsigned i=0;i<h->e_shnum;i++)if(sh[i].sh_type==SHT_REL){
        const Elf32_Rel *r=(const void *)(file+sh[i].sh_offset);
        const Elf32_Shdr *st=&sh[sh[i].sh_link];const Elf32_Sym *sy=(const void *)(file+st->sh_offset);
        const char *strings=(const void *)(file+sh[st->sh_link].sh_offset);
        for(unsigned j=0;j<sh[i].sh_size/sizeof(*r);j++){
            unsigned type=ELF32_R_TYPE(r[j].r_info);const Elf32_Sym *s=&sy[ELF32_R_SYM(r[j].r_info)];
            const char *name=strings+s->st_name;void *value=import(name);
            assert(r[j].r_offset>=0x10000 && r[j].r_offset+4<=0x210000);
            if(type==R_ARM_COPY){assert(!strcmp(name,"stderr") && s->st_size==4);memcpy((void *)(uintptr_t)r[j].r_offset,value,4);}
            else {assert(type==R_ARM_GLOB_DAT || type==R_ARM_JUMP_SLOT);*(uintptr_t *)(uintptr_t)r[j].r_offset=(uintptr_t)value;}
        }
    }

 assert(symbol(file,"xintiao")==0x13fd4);patch(symbol(file,"gpio_read_ioc11"),gpio);patch(symbol(file,"mui_Setflash"),refresh);
 __builtin___clear_cache((void *)0x10000,(void *)0x210000);
 unsigned shared[115]={0};shared[1]=1;*(uintptr_t *)symbol(file,"shm")=(uintptr_t)shared;
 int *level=(void *)symbol(file,"ADC_LEVEL"),*ticks=(void *)symbol(file,"modify_time"),*threshold=(void *)symbol(file,"ADC_LEVE"),*debug=(void *)symbol(file,"ADC_DEBUG");
 const int card[5]={318,310,300,290,275};memcpy(threshold,card,sizeof(card));*(int *)symbol(file,"USE_HDMI_OUT")=0;
 void (*heartbeat)(void)=(void *)symbol(file,"xintiao");unsigned cases=0;
 strcpy((char *)symbol(file,"work_path"),"/usr/retro/");memset(threshold,0,sizeof(card));*ticks=0;heartbeat();
 assert(!memcmp(threshold,card,sizeof(card)));puts("PASS exact ARM config path and five parsed card thresholds");
 for(unsigned bits=0;bits<4;bits++){gpio_a=bits&1;gpio_b=(bits>>1)&1;
  for(unsigned marker=0;marker<2;marker++)for(unsigned value=0;value<1024;value++)for(int previous=0;previous<6;previous++){
   raw=value|(marker?0x8000:0);*ticks=511;*level=previous;unsigned before=read_calls;heartbeat();assert(read_calls==before+1);
   unsigned scaled=(value*330)/1024;int want=reference(scaled,previous,card);
   if(*debug!=(int)scaled||*level!=want){fprintf(stderr,"Mismatch raw=%u previous=%d gpio=%u%u got=%d scaled=%d expected=%d\n",raw,previous,gpio_a,gpio_b,*level,*debug,want);return 3;}cases++;
  }
 }
 printf("PASS exact ARM stock sampler %u raw/timeout-flag/previous-state/GPIO combinations\n",cases);
 gpio_a=gpio_b=0;raw=0;*ticks=511;*level=3;heartbeat();assert(*level==-1);
 raw=1000;read_error=1;*ticks=511;*level=3;heartbeat();printf("Failed read ignored: classified_level=%d scaled=%d read_return=-1\n",*level,*debug);assert(*level==-1&&*debug==0);
 read_error=0;start_error=1;*ticks=511;*level=3;heartbeat();assert(*level==0);puts("PASS failed channel-start ignored despite subsequent successful read");
 start_error=0;open_error=1;*ticks=511;*level=3;heartbeat();assert(*level==0);puts("PASS failed ADC open still proceeds to ioctl/read and classification");
 unsigned before=read_calls;*ticks=511;*level=-1;gpio_a=gpio_b=1;heartbeat();assert(read_calls==before&&*level==-1);puts("PASS negative low state suppresses subsequent ADC/GPIO resampling even after plug-in");
 open_error=0;gpio_a=gpio_b=0;raw=0;*ticks=127;*level=0;heartbeat();assert(*level==0);puts("PASS first 128-call low sample cannot enter critical state");
 *ticks=255;*level=0;heartbeat();assert(*level==-1);puts("PASS second 256-call low sample can enter critical state");
 *(int *)symbol(file,"USE_HDMI_OUT")=1;*ticks=511;*level=0;heartbeat();assert(*level==0);puts("PASS HDMI suppresses critical state");
 patch(symbol(file,"GetWorkPath"),workpath);patch(symbol(file,"get_warning_data"),warning_data);
 patch(symbol(file,"DispFrame"),display);patch(symbol(file,"LCM_LED"),backlight);patch(symbol(file,"gpChunkMemFree"),release);
 *level=-1;if(!setjmp(shutdown_boundary))((void (*)(void))symbol(file,"mui_WaitNMI"))();
 assert(warning_steps==31);puts("PASS exact ARM menu critical state -> warning -> five-second delay -> backlight off -> intercepted poweroff; no hardware touched");return 0;
}
