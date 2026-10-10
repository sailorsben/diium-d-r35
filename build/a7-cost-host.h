/* Included only in the isolated measurement runner. Bounded in-memory records.
 * Sysfs reads and record-copy work are outside retro_run and reported. */
#ifndef D35_COST_HOST_H
#define D35_COST_HOST_H
#include "../a7-cost.h"
#include "board.h"
#include "audio-pipe.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/syscall.h>
#include <time.h>
#include <sys/utsname.h>
#define D35_HOST_FRAMES 500u
struct cost_host_record {
    unsigned frame;long before_khz,after_khz;
    uint64_t wall,cpu,observer_ns,ppu,before_ns,after_ns;
    struct audio_pipe_stats audio;
    struct board_video_metrics video;
    struct d35_cost_frame cost;
};
static struct {
    struct cost_host_record row[D35_HOST_FRAMES];
    unsigned count,mode,started,overflow;
    int freq_fd;long original_min,pinned_max;unsigned pinned;
    char policy[256],min_path[300],freq_path[300],pin_status[128];
    char governor[80],cpu_online[80],kernel[256];
    uint64_t before_observer,frame_observer;
} cost_host;
static uint64_t cost_host_ns(void)
{
    struct timespec t={0,0};
    if(syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t)) return 0;
    return (uint64_t)t.tv_sec*1000000000ull+(uint64_t)t.tv_nsec;
}
static int cost_text(const char *path,char *out,size_t size)
{
    int fd=open(path,O_RDONLY|O_CLOEXEC);ssize_t n;
    if(fd<0) { snprintf(out,size,"unavailable_errno_%d",errno);return -1; }
    n=read(fd,out,size-1);close(fd);
    if(n<=0) { snprintf(out,size,"unavailable_errno_%d",errno);return -1; }
    out[n]=0;while(n && (out[n-1]=='\n'||out[n-1]=='\r'))out[--n]=0;return 0;
}
static long cost_parse(const char *t)
{
    long n=0;if(!*t)return -1;
    while(*t && *t!='\n') {
        if(*t<'0'||*t>'9'||n>100000000)return -1;
        n=n*10+(*t++-'0');
    }
    return n;
}
static long cost_number(const char *path)
{ char t[80];if(cost_text(path,t,sizeof(t)))return -1;return cost_parse(t); }
static long cost_frequency(void)
{
    char t[80];ssize_t n;
    if(cost_host.freq_fd<0 || lseek(cost_host.freq_fd,0,SEEK_SET)<0)return -1;
    n=read(cost_host.freq_fd,t,sizeof(t)-1);if(n<=0)return -1;t[n]=0;
    return cost_parse(t);
}
static int cost_write_number(const char *path,long v)
{
    char t[80];int n=snprintf(t,sizeof(t),"%ld\n",v),fd=open(path,O_WRONLY|O_CLOEXEC);
    ssize_t written;if(fd<0)return -1;written=write(fd,t,n);close(fd);return written==n?0:-1;
}
static void cost_host_start(void)
{
    const char *mode=getenv("D35_COST_MODE");struct utsname u;char path[300];
    memset(&cost_host,0,sizeof(cost_host));cost_host.freq_fd=-1;cost_host.started=1;
    cost_host.mode=mode?(unsigned)cost_parse(mode):0;
    if(cost_host.mode>3) cost_host.mode=0;
    if(!uname(&u))snprintf(cost_host.kernel,sizeof(cost_host.kernel),"%.70s %.70s %.70s",u.sysname,u.release,u.machine);
    cost_text("/sys/devices/system/cpu/online",cost_host.cpu_online,sizeof(cost_host.cpu_online));
    strcpy(cost_host.policy,"/sys/devices/system/cpu/cpufreq/policy0");
    snprintf(path,sizeof(path),"%s/scaling_max_freq",cost_host.policy);
    cost_host.pinned_max=cost_number(path);
    if(cost_host.pinned_max<=0) {
        strcpy(cost_host.policy,"/sys/devices/system/cpu/cpu0/cpufreq");
        snprintf(path,sizeof(path),"%s/scaling_max_freq",cost_host.policy);
        cost_host.pinned_max=cost_number(path);
    }
    snprintf(cost_host.min_path,sizeof(cost_host.min_path),"%s/scaling_min_freq",cost_host.policy);
    cost_host.original_min=cost_number(cost_host.min_path);
    snprintf(path,sizeof(path),"%s/scaling_governor",cost_host.policy);
    cost_text(path,cost_host.governor,sizeof(cost_host.governor));
    snprintf(cost_host.freq_path,sizeof(cost_host.freq_path),"%s/scaling_cur_freq",cost_host.policy);
    cost_host.freq_fd=open(cost_host.freq_path,O_RDONLY|O_CLOEXEC);
    if(cost_host.freq_fd<0) {
        snprintf(cost_host.freq_path,sizeof(cost_host.freq_path),"%s/cpuinfo_cur_freq",cost_host.policy);
        cost_host.freq_fd=open(cost_host.freq_path,O_RDONLY|O_CLOEXEC);
    }
    strcpy(cost_host.pin_status,"not_exposed_or_not_writable");
    if(!strcmp(cost_host.cpu_online,"0") && cost_host.original_min>0 && cost_host.pinned_max>=cost_host.original_min) {
        if(!cost_write_number(cost_host.min_path,cost_host.pinned_max)) {
            cost_host.pinned=1;
            snprintf(cost_host.pin_status,sizeof(cost_host.pin_status),"min_set_to_existing_max_%ld_readback_%ld",cost_host.pinned_max,cost_number(cost_host.min_path));
        } else snprintf(cost_host.pin_status,sizeof(cost_host.pin_status),"pin_write_errno_%d",errno);
    }
}
static unsigned cost_host_mode(unsigned frame)
{ return cost_host.mode==1?(frame%8==5?1:0):cost_host.mode==3?(frame==320?3:0):cost_host.mode; }
static void cost_host_before(unsigned frame)
{
    uint64_t began=cost_host_ns();
    if(frame<D35_HOST_FRAMES) { cost_host.row[frame].before_ns=began;cost_host.row[frame].before_khz=cost_frequency(); }
    cost_host.frame_observer=cost_host_ns()-began;
}
static void cost_host_after(void (*end)(struct d35_cost_frame *),unsigned frame,uint64_t wall,uint64_t cpu,uint64_t ppu)
{
    uint64_t began=cost_host_ns();
    if(frame>=D35_HOST_FRAMES) { ++cost_host.overflow;return; }
    struct cost_host_record *r=&cost_host.row[frame];
    r->frame=frame;r->wall=wall;r->cpu=cpu;r->ppu=ppu;r->after_khz=cost_frequency();end(&r->cost);
    audio_pipe_stats(&r->audio);board_video_metrics(&r->video,0);
    r->observer_ns=cost_host.frame_observer+cost_host_ns()-began;
    r->after_ns=cost_host_ns();
    cost_host.count=frame+1;
}
static void cost_host_finish(const char *dir,int mock,int failed,uint64_t runs)
{
    char path[1300],restore[80]="not_changed";FILE *out;unsigned i,k;
    if(!cost_host.started)return;
    if(cost_host.pinned) {
        int rc=cost_write_number(cost_host.min_path,cost_host.original_min);
        snprintf(restore,sizeof(restore),"write_rc_%d_readback_%ld",rc,cost_number(cost_host.min_path));
    }
    if(cost_host.freq_fd>=0)close(cost_host.freq_fd);
    snprintf(path,sizeof(path),"%s/unit-cost.csv",dir);out=fopen(path,"w");
    if(!out)return;
    fprintf(out,"#contract_fixture=%d\n",getenv("D35_COST_CONTRACT_FIXTURE")!=NULL);
    fprintf(out,"#suite=1.19-cost1\n#mock=%d\n#failed=%d\n#runs=%llu\n#mode=%u\n#overflow=%u\n#kernel=%s\n#cpu_online=%s\n#frequency_path=%s\n#governor=%s\n#pin=%s\n#restore=%s\n#logging=bounded_RAM_flush_after_worker_stop\n#timers=kernel_syscall_thread_cpu_and_monotonic\n#costs=instrumentation_included_no_subtraction\n",mock,failed,(unsigned long long)runs,cost_host.mode,cost_host.overflow,cost_host.kernel,cost_host.cpu_online,cost_host.freq_path,cost_host.governor,cost_host.pin_status,restore);
    fputs("type,frame,kind,iterations,shape,warm,cpu_ns,wall_ns,freq_before_khz,freq_after_khz,observer_ns\n",out);
    for(i=0;i<cost_host.count;i++) {
        const struct cost_host_record *r=&cost_host.row[i];const struct d35_cost_frame *f=&r->cost;
        fprintf(out,"frame,%u,%u,1,0,0,%llu,%llu,%ld,%ld,%llu\n",i,f->mode,(unsigned long long)r->cpu,(unsigned long long)r->wall,r->before_khz,r->after_khz,(unsigned long long)r->observer_ns);
        fprintf(out,"checkpoint,%u,0,1,0,0,%llu,%llu,%ld,%ld,0\n",i,(unsigned long long)r->before_ns,(unsigned long long)r->after_ns,r->before_khz,r->after_khz);
        fprintf(out,"ppu,%u,0,1,0,0,%llu,0,%ld,%ld,0\n",i,(unsigned long long)r->ppu,r->before_khz,r->after_khz);
        fprintf(out,"timer_control,%u,0,64,0,0,%llu,%llu,%ld,%ld,0\n",i,(unsigned long long)f->clock_loop_cpu_ns,(unsigned long long)f->clock_loop_wall_ns,r->before_khz,r->after_khz);
        fprintf(out,"service,%u,%u,%u,%u,%u,%llu,%llu,%ld,%ld,%u\n",i,r->audio.epoch,r->audio.appl_ptr,r->audio.hw_ptr,r->audio.state,(unsigned long long)r->audio.epoch_transferred,(unsigned long long)r->audio.observed_ns,r->before_khz,r->after_khz,r->audio.playable);
        fprintf(out,"workers,%u,0,0,0,0,%llu,%llu,%ld,%ld,%llu\n",i,(unsigned long long)r->audio.worker_cpu_ns,(unsigned long long)r->video.worker_cpu_ns,r->before_khz,r->after_khz,(unsigned long long)r->video.submitted);
        for(k=0;k<D35_COST_PHASES;k++)fprintf(out,"phase,%u,%u,%llu,0,0,%llu,0,%ld,%ld,0\n",i,k,(unsigned long long)f->phase_entries[k],(unsigned long long)f->cpu_ns[k],r->before_khz,r->after_khz);
        fprintf(out,"counts,%u,0,%llu,%llu,%llu,%llu,%llu,%ld,%ld,%u\n",i,(unsigned long long)f->ppu_entries,(unsigned long long)f->row_misses,(unsigned long long)f->row_hits,(unsigned long long)f->clock_calls,(unsigned long long)f->clock_errors,r->before_khz,r->after_khz,f->overflow);
        fprintf(out,"row_sampling,%u,0,%llu,%llu,%u,0,0,%ld,%ld,0\n",i,(unsigned long long)f->sampled_misses,(unsigned long long)f->sampled_hits,f->mode==3?1u:64u,r->before_khz,r->after_khz);
        for(k=0;k<D35_B_KINDS;k++)fprintf(out,"calls,%u,%u,%llu,0,0,0,0,%ld,%ld,0\n",i,k,(unsigned long long)f->path_calls[k],r->before_khz,r->after_khz);
        for(k=0;k<f->samples;k++) {
            const struct d35_cost_sample *b=&f->sample[k];
            fprintf(out,"bench,%u,%u,%u,%u,%u,%llu,%llu,%ld,%ld,0\n",i,b->kind,b->iterations,b->shape,b->warm_iterations,(unsigned long long)b->cpu_ns,(unsigned long long)b->wall_ns,r->before_khz,r->after_khz);
        }
    }
    fflush(out);fsync(fileno(out));fclose(out);cost_host.started=0;
}
#endif
