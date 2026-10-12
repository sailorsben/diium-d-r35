/* Frame-boundary observer only. Included costs are never subtracted. */
#ifndef D35_PAIR_HOST_H
#define D35_PAIR_HOST_H
#include "frequency-host.h"
struct pair_row {
    unsigned frame;
    uint64_t cpu,wall,admission,observer,step,generated;
    long before_khz,after_khz;
    struct audio_pipe_stats audio;
    struct board_video_metrics video;
};
static struct pair_row pair_rows[500];
static unsigned pair_count,pair_start;
static uint64_t pair_observer;
static long pair_before_khz;
static void pair_begin(void) {
    memset(pair_rows,0,sizeof(pair_rows));pair_count=0;
    pair_start=(unsigned)cost_parse(getenv("D35_PAIR_START"));cost_host_start();
}
static void pair_before(void) {
    uint64_t n=cost_host_ns();pair_before_khz=cost_frequency();pair_observer=cost_host_ns()-n;
}
static void pair_after(unsigned local,uint64_t cpu,uint64_t wall,uint64_t admission,uint64_t step,uint64_t generated) {
    uint64_t n=cost_host_ns();
    if(local>=500)return;
    struct pair_row *r=&pair_rows[local];r->frame=pair_start+local;r->cpu=cpu;r->wall=wall;r->admission=admission;
    r->before_khz=pair_before_khz;r->after_khz=cost_frequency();r->generated=generated;
    audio_pipe_stats(&r->audio);board_video_metrics(&r->video,0);
    r->observer=pair_observer+cost_host_ns()-n;r->step=cost_host_ns()-step;pair_count=local+1;
}
static void pair_finish(const char *dir,int mock,int failed) {
    char path[1300],restore[80]="unchanged";FILE *f;
    if(!cost_host.started)return;
    if(cost_host.pinned) {
        int rc=cost_write_number(cost_host.min_path,cost_host.original_min);
        snprintf(restore,sizeof(restore),"rc_%d_readback_%ld",rc,cost_number(cost_host.min_path));
    }
    if(cost_host.freq_fd>=0)close(cost_host.freq_fd);
    snprintf(path,sizeof(path),"%s/pair.csv",dir);f=fopen(path,"w");if(!f)return;
    fprintf(f,"#suite=1.19-pair1\n#mock=%d\n#failed=%d\n#start=%u\n#kernel=%s\n#cpu_online=%s\n#governor=%s\n#pin=%s\n#restore=%s\n#logging=RAM_until_workers_join\n#phase_clocks=disabled\n#costs=observer_included_no_subtraction\n",
        mock,failed,pair_start,cost_host.kernel,cost_host.cpu_online,cost_host.governor,cost_host.pin_status,restore);
    fputs("frame,cpu_ns,wall_ns,admission_ns,observer_ns,step_ns,freq_before_khz,freq_after_khz,native_generated,accepted,enqueued,remaining,playable,state,epoch,appl,hw,xfer,observed_ns,audio_worker_cpu_ns,video_worker_cpu_ns,submitted,flipped\n",f);
    for(unsigned i=0;i<pair_count;i++) {
        const struct pair_row *r=&pair_rows[i];const struct audio_pipe_stats *a=&r->audio;
        fprintf(f,"%u,%llu,%llu,%llu,%llu,%llu,%ld,%ld,%llu,%llu,%llu,%u,%u,%u,%u,%u,%u,%llu,%llu,%llu,%llu,%llu,%llu\n",
            r->frame,(unsigned long long)r->cpu,(unsigned long long)r->wall,(unsigned long long)r->admission,(unsigned long long)r->observer,(unsigned long long)r->step,
            r->before_khz,r->after_khz,(unsigned long long)r->generated,(unsigned long long)a->accepted,(unsigned long long)a->enqueued,a->remaining,a->playable,a->state,a->epoch,a->appl_ptr,a->hw_ptr,
            (unsigned long long)a->epoch_transferred,(unsigned long long)a->observed_ns,(unsigned long long)a->worker_cpu_ns,(unsigned long long)r->video.worker_cpu_ns,(unsigned long long)r->video.submitted,(unsigned long long)r->video.flipped);
    }
    fflush(f);fsync(fileno(f));fclose(f);cost_host.started=0;
}
#endif
