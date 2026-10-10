/* Execute the real callbacks/reporting and replay independent returned costs. */
#define main runner_contract_main
#include "runner-check.c"
#undef main
/* Build-host headers redirect sscanf to a newer ABI than the device libc. */
extern int d35_sscanf(const char *,const char *,...) __asm__("__isoc99_sscanf");
int main(int argc,char **argv)
{
    unsigned offset,pass,i,coverage=0; char line[1024];
    uint64_t costs[24][2]; unsigned count=0; FILE *input;
    uLong reference=0; uint64_t frames=0;
    assert(argc==3);
    { char *args[]={argv[0],argv[1],NULL}; assert(!runner_contract_main(2,args)); }
    input=fopen(argv[2],"r"); assert(input);
    while(fgets(line,sizeof(line),input)) {
        unsigned index,epoch,sampled; unsigned long long run,wall,cpu;
        if(d35_sscanf(line,"frame_cost_%u=%llu,%u,%u,%llu,%llu",&index,&run,&epoch,&sampled,&wall,&cpu)==6) {
            assert(index==count && count<24 && !sampled && epoch==2);
            costs[count][0]=wall;costs[count++][1]=cpu;
        }
    }
    fclose(input);assert(count==24);
    for(offset=0;offset<64;offset++) {
        struct d35_focus_policy policy={offset,0,0}; unsigned samples=0,last=0;
        for(i=0;i<23;i++) {
            unsigned reason=d35_focus_next(&policy);
            if(reason) { if(samples) assert(i-last<=8);last=i;++samples; }
            d35_focus_observe(&policy,reason!=0,costs[i][0],costs[i][1]);
        }
        assert(samples>=2 && policy.hot_remaining);coverage+=samples;
    }
    { struct d35_focus_policy policy={0,0,0};
      for(i=0;i<256;i++) { unsigned reason=d35_focus_next(&policy);
        assert(reason==(i%64==3?1u:0u));
        d35_focus_observe(&policy,reason!=0,reason?999999999u:10000000u,10000000u); }
      assert(!policy.hot_remaining && !policy.triggers); }
    for(pass=0;pass<2;pass++) {
        int16_t data[535*2];
        for(i=0;i<ARRAY_SIZE(data);i++) data[i]=(int16_t)(i*117u);
        memset(&s,0,sizeof(s));s.input_rate=32040;s.output_rate=44100;s.audio_ready=true;
        s.focus_active=pass;error_text[0]=0; fragmented=0;sink_frames=0;sink_crc=crc32(0,NULL,0);
        audio_pipe_init();assert(!audio_pipe_start());assert(audio_batch(data,535)==535);
        audio_pipe_stop(1);pump_audio();assert(!s.failed);
        if(!pass) { reference=sink_crc;frames=sink_frames; }
        else { assert(sink_crc==reference && sink_frames==frames);assert(s.focus_audio_calls==1 && s.focus_audio_cpu>0); }
    }
    memset(&s,0,sizeof(s));
    for(i=0;i<64;i++) { s.frame_costs[i]=(struct frame_cost){.run=i+1,.wall=999999999u,.cpu=888888888u,
        .apu=333333333u,.ppu=333333333u,.audio=7777777u,.video=7777777u,.admission=7777777u,
        .epoch=2,.sampled=1,.audio_cpu=7777777u,.video_cpu=7777777u,.reason=2,.audio_calls=2,.video_calls=1}; }
    s.frame_cost_count=64;s.run_hist[127]=64;
    snprintf(s.report_path,sizeof(s.report_path),"%s/focus-report.txt",argv[1]);
    report_to(s.report_path,"fixture",0);
    { size_t n;char *raw=read_file(s.report_path,32768,&n);assert(raw);
      assert(strstr(raw,"frame_cost_63=") && strstr(raw,"focus_cost_63="));
      assert(strstr(raw,"core_wall_bin_127ms=64") && strstr(raw,"build_version=1.19-focus1"));free(raw); }
    printf("PASS: all64 cadence offsets cover real1.19 failing-cost window with at least two samples; %u samples total\n",coverage);
    puts("PASS: sampled overhead cannot trigger or extend pressure profiling; measured callback PCM equals unmeasured callback PCM");
    puts("PASS: real report preserves all64 frame/CPU callback records and histogram without truncation");
    return 0;
}
