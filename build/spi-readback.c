/* Fixed read-only capture for the measured c8 40 17 SPI NOR family.
 * Two full 8-MiB passes, ordinary 03 + 24-bit address. No flash writer.
 * Keep the physically qualified identification/ownership code unchanged. */
#pragma push_macro("main")
#undef main
#define main identification_entry
#include "spi-identify.c"
#pragma pop_macro("main")

#define FLASH_BYTES (8u*1024u*1024u)
#define BLOCK_BYTES 4096u
#ifndef READBACK_DEADLINE_NS
#define READBACK_DEADLINE_NS 240000000000ull
#endif
typedef struct {
    Result chip;
    uint32_t bytes[2],crc[2],nonzero[2],nonff[2],nona5[2];
    uint64_t elapsed_ns;
    int compared;
} Snapshot;

static uint32_t crc_bytes(uint32_t crc,const unsigned char *data,unsigned n) {
    for(unsigned i=0;i<n;i++) {
        crc^=data[i];
        for(unsigned b=0;b<8;b++)crc=(crc>>1)^((crc&1)?0xedb88320u:0);
    }
    return crc;
}
static int write_all(int fd,const unsigned char *data,unsigned length) {
    unsigned done=0;
    while(done<length) {
        ssize_t n=write(fd,data+done,length-done);
        if(n<0&&errno==EINTR)continue;
        if(n<=0)return n<0?errno:EIO;
        done+=(unsigned)n;
    }
    return 0;
}
static int previous(int fd,uint32_t offset,unsigned char *data) {
    unsigned done=0;
    while(done<BLOCK_BYTES) {
        ssize_t n=pread64(fd,data+done,BLOCK_BYTES-done,(off64_t)offset+done);
        if(n<0&&errno==EINTR)continue;
        if(n<=0)return n<0?errno:EIO;
        done+=(unsigned)n;
    }
    return 0;
}
static int read_block(int fd,uint32_t address,unsigned char *data,Result *r) {
    if(address>=FLASH_BYTES||address%BLOCK_BYTES)return EINVAL;
    unsigned char command[4]={0x03,(unsigned char)(address>>16),
                             (unsigned char)(address>>8),(unsigned char)address};
    struct spi_ioc_transfer t[2];memset(t,0,sizeof(t));memset(data,0xa5,BLOCK_BYTES);
    uint32_t speed=r->speed<1000000u?r->speed:1000000u;
    t[0].tx_buf=(uintptr_t)command;t[0].len=4;t[0].speed_hz=speed;t[0].bits_per_word=8;t[0].tx_nbits=1;
    t[1].rx_buf=(uintptr_t)data;t[1].len=BLOCK_BYTES;t[1].speed_hz=speed;t[1].bits_per_word=8;t[1].rx_nbits=1;
    r->operations++;int got=ioctl(fd,SPI_IOC_MESSAGE(2),t);
    if(got<0)return errno;
    return got==(int)(BLOCK_BYTES+4)?0:EIO;
}
static int check_chip(int fd,Result *r) {
    int had=r->operations;uint32_t mode=r->mode,speed=r->speed;unsigned char bits=r->bits;
    int e=owners(r);if(e)return e;
    e=identify(fd,r);if(e)return e;
    if(had&&(r->mode!=mode||r->speed!=speed||r->bits!=bits))return ESTALE;
    const unsigned char wanted[6]={0xc8,0x40,0x17,0xc8,0x40,0x17};
    for(unsigned i=0;i<3;i++)if(memcmp(r->id[i],wanted,6))return ENODEV;
    return 0;
}
static int progress(FILE *report,Snapshot *s,unsigned pass) {
    fprintf(report,"{\"kind\":\"progress\",\"pass\":%u,\"bytes\":%u,\"crc32_so_far\":\"%08x\"}\n",
            pass,s->bytes[pass],s->crc[pass]^0xffffffffu);
    fflush(report);return ferror(report)||fsync(fileno(report))?EIO:0;
}
static int capture(int fd,int bundle,FILE *report,Snapshot *s) {
    unsigned char data[BLOCK_BYTES],old[BLOCK_BYTES];Result *r=&s->chip;
    for(unsigned pass=0;pass<2;pass++) {
        stage(r,"identify-pass");int e=check_chip(fd,r);if(e)return e;
        s->crc[pass]=0xffffffffu;stage(r,pass?"read-pass-2":"read-pass-1");
        for(uint32_t address=0;address<FLASH_BYTES;address+=BLOCK_BYTES) {
            e=read_block(fd,address,data,r);if(e)return e;
            if(pass) {
                e=previous(bundle,address,old);if(e)return e;
                if(memcmp(data,old,BLOCK_BYTES)) { stage(r,"pass-mismatch");return EILSEQ; }
            }
            e=write_all(bundle,data,BLOCK_BYTES);if(e)return e;
            s->bytes[pass]+=BLOCK_BYTES;s->crc[pass]=crc_bytes(s->crc[pass],data,BLOCK_BYTES);
            for(unsigned j=0;j<BLOCK_BYTES;j++) {
                s->nonzero[pass]+=data[j]!=0;s->nonff[pass]+=data[j]!=0xff;s->nona5[pass]+=data[j]!=0xa5;
            }
            if(!(s->bytes[pass]%(1024u*1024u))) {
                if(fsync(bundle))return errno;
                e=progress(report,s,pass);if(e)return e;
            }
        }
        s->crc[pass]^=0xffffffffu;
        if(!s->nonzero[pass]||!s->nonff[pass]||!s->nona5[pass])return ENODATA;
    }
    stage(r,"identify-final");int e=check_chip(fd,r);if(e)return e;
    if(fsync(bundle))return errno;
    s->compared=1;stage(r,"readback-complete");return 0;
}
static void snapshot(int bundle,FILE *report,Snapshot *s) {
    Result *r=&s->chip;stage(r,"owners-before");if((r->error=owners(r)))return;
    char path[PATH_MAX];snprintf(path,sizeof(path),"%s/dev/spidev0.0",root);struct stat64 st;
    stage(r,"device-identity");
    if(lstat(path,&st)) { r->error=errno;return; }
    if(!S_ISCHR(st.st_mode)||major(st.st_rdev)!=153||minor(st.st_rdev)!=0) { r->error=EPERM;return; }
    int fd=open(path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);if(fd<0) { r->error=errno;return; }
    if(fstat(fd,&st)||!S_ISCHR(st.st_mode)||major(st.st_rdev)!=153||minor(st.st_rdev)!=0)r->error=EPERM;
    else if(flock(fd,LOCK_EX|LOCK_NB))r->error=errno;
    else {
        stage(r,"owners-after");r->error=owners(r);
        if(!r->error)r->error=capture(fd,bundle,report,s);
    }
    close(fd);
}
static int summary(FILE *f,Snapshot *s,int timeout,int pending) {
    Result *r=&s->chip;
    fprintf(f,"{\"kind\":\"result\",\"version\":1,\"errno\":%d,\"stage\":\"%s\",\"owner_pid\":%d,\"operations\":%d,\"capacity_bytes\":%u,\"block_bytes\":%u,\"bytes\":[%u,%u],\"crc32\":[\"%08x\",\"%08x\"],\"byte_compared\":%s,\"elapsed_ns\":%llu,\"mode\":%u,\"bits\":%u,\"default_speed_hz\":%u,\"transfer_speed_limit_hz\":1000000,\"status_before\":%u,\"status_after\":%u,\"ids\":[",
            r->error,r->stage,r->owner_pid,r->operations,FLASH_BYTES,BLOCK_BYTES,s->bytes[0],s->bytes[1],s->crc[0],s->crc[1],s->compared?"true":"false",(unsigned long long)s->elapsed_ns,r->mode,r->bits,r->speed,r->status_before,r->status_after);
    for(unsigned i=0;i<3;i++) {
        if(i)fputc(',',f);
        fputc('"',f);for(unsigned j=0;j<6;j++)fprintf(f,"%02x",r->id[i][j]);fputc('"',f);
    }
    fprintf(f,"],\"timed_out\":%s,\"reap_pending\":%s,\"flash_writes\":false,\"global_config_writes\":false}\n",timeout?"true":"false",pending?"true":"false");
    fflush(f);return ferror(f)||fsync(fileno(f));
}
int main(int argc,char **argv) {
    if(argc!=3||strlen(argv[1])>PATH_MAX-512||strlen(argv[2])>PATH_MAX-64)return 2;
    snprintf(root,sizeof(root),"%s",!strcmp(argv[1],"/")?"":argv[1]);
    if(mkdir(argv[2],0700))return 2;
    char report_path[PATH_MAX],bundle_path[PATH_MAX];
    snprintf(report_path,sizeof(report_path),"%s/report.jsonl",argv[2]);
    snprintf(bundle_path,sizeof(bundle_path),"%s/captures.bin",argv[2]);
    FILE *report=fopen(report_path,"wx");if(!report)return 2;
    int bundle=open(bundle_path,O_RDWR|O_CREAT|O_EXCL|O_CLOEXEC,0600);if(bundle<0)return 2;
    int directory=open(argv[2],O_RDONLY|O_DIRECTORY);
    fprintf(report,"{\"kind\":\"start\",\"version\":1,\"expected_jedec\":\"c84017\",\"capacity_bytes\":%u,\"passes\":2}\n",FLASH_BYTES);
    fflush(report);
    if(directory<0||ferror(report)||fsync(bundle)||fsync(fileno(report))||fsync(directory))return 2;
    close(directory);int pipefd[2];if(pipe(pipefd))return 2;
    uint64_t begin=now_ns(),end=begin+READBACK_DEADLINE_NS;pid_t pid=fork();if(pid<0)return 2;
    if(!pid) {
        close(pipefd[0]);Snapshot s={0};snapshot(bundle,report,&s);s.elapsed_ns=now_ns()-begin;
        if(fclose(report)||close(bundle))s.chip.error=EIO;
        (void)!write(pipefd[1],&s,sizeof(s));close(pipefd[1]);_exit(0);
    }
    fclose(report);close(bundle);close(pipefd[1]);Snapshot s={0};int status=0,timeout=0,pending=0;pid_t done;
    while(!(done=waitpid(pid,&status,WNOHANG))&&now_ns()<end)delay();
    if(!done) {
        timeout=1;kill(pid,SIGKILL);end=now_ns()+250000000ull;
        while(!(done=waitpid(pid,&status,WNOHANG))&&now_ns()<end)delay();
        s.chip.error=ETIMEDOUT;stage(&s.chip,"deadline");
        if(!done) {
            pending=1;report=fopen(report_path,"a");if(report) { summary(report,&s,timeout,pending);fclose(report); }
            do { done=waitpid(pid,&status,0); } while(done<0&&errno==EINTR);
        }
    } else if(done<0||!WIFEXITED(status)||WEXITSTATUS(status)||read(pipefd[0],&s,sizeof(s))!=(ssize_t)sizeof(s)) {
        s.chip.error=EIO;stage(&s.chip,"child-result");
    }
    close(pipefd[0]);s.elapsed_ns=now_ns()-begin;report=fopen(report_path,"a");if(!report)return 2;
    int failed=summary(report,&s,timeout,pending);if(fclose(report))failed=1;
    return failed||s.chip.error?1:0;
}
