/* Included after the runner aggregate. Flush only after both workers stop. */
static void quick_flush(void)
{
    char path[1300];FILE *f;
    if(!s.save_dir[0])return;
    snprintf(path,sizeof(path),"%s/phases.csv",s.save_dir);
    f=fopen(path,"w");if(!f)return;
    fprintf(f,"#clock=kernel_THREAD_CPUTIME_ID\n#logging=RAM_until_audio_join_display_idle\n#costs=included_never_subtracted\n#profile=%d\n#sample_stride=8\n#clock_loop_mean_ns=%llu\n#nested=APU_includes_audio_callback_PPU_may_include_video_callback\n",
        getenv("D35_QUICK_PROFILE")!=NULL,(unsigned long long)s.focus_clock_mean_ns);
    fputs("frame,sampled,core_cpu_ns,core_wall_ns,ppu_cpu_ns,apu_inclusive_cpu_ns,audio_callback_cpu_ns,video_callback_cpu_ns,audio_callbacks,video_callbacks,admission_wall_ns\n",f);
    for(unsigned i=0;i<s.quick_count;i++){
        const struct frame_cost *r=&s.quick_rows[i];
        fprintf(f,"%llu,%u,%llu,%llu,%llu,%llu,%llu,%llu,%u,%u,%llu\n",
            (unsigned long long)(r->run-1),r->sampled,
            (unsigned long long)r->cpu,(unsigned long long)r->wall,
            (unsigned long long)r->ppu,(unsigned long long)r->apu,
            (unsigned long long)r->audio_cpu,(unsigned long long)r->video_cpu,
            r->audio_calls,r->video_calls,(unsigned long long)r->admission);
    }
    fflush(f);fsync(fileno(f));fclose(f);
}
