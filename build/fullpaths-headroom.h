/* Included in owned pair-host after definitions. Write only after worker joins.
 * Conservative service proxy adds all worker CPU to unpaced wall: overlap may
 * be counted twice. Never subtract observer clocks or claim physical evidence
 * from a mock. Pure intentional pacing is separately identified at the wait. */
#ifndef FULLPATHS_HEADROOM_H
#define FULLPATHS_HEADROOM_H
static int full_u64_compare(const void *a,const void *b) {
 uint64_t x=*(const uint64_t *)a,y=*(const uint64_t *)b;return (x>y)-(x<y);
}
static void full_headroom(const char *dir,int mock,int failed) {
 if(getenv("D35_FULL_HOST_FIXTURE"))mock=1;
 uint64_t service[1200],cpu[1200],sum=0,observer=0,prev_a=0,prev_v=0;
 unsigned count=0,over=0,margin_over=0,invalid=0;
 char path[1300];struct board_video_metrics final;board_video_metrics(&final,0);
 struct audio_pipe_stats audio;audio_pipe_stats(&audio);
 for(unsigned i=0;i<pair_count;i++){
  const struct pair_row *r=&pair_rows[i];
  uint64_t a=r->audio.worker_cpu_ns,v=r->video.worker_cpu_ns;
  int valid=a>=prev_a&&v>=prev_v&&r->pace_wait<=r->step;
  uint64_t active=r->step>=r->pace_wait?r->step-r->pace_wait:r->step;
  if(valid)active+=a-prev_a+v-prev_v;else invalid++;
  prev_a=a;prev_v=v;
  if(!r->pointer_valid)invalid++;
  observer+=r->observer+r->identity_observer;
  if(i<120)continue; /* Warm distributions only; raw rows retain all calls. */
  service[count]=active;cpu[count]=r->cpu;sum+=active;count++;
  if(active>16688154ull)over++;
  if(active>13350523ull)margin_over++;
 }
 qsort(service,count,sizeof(*service),full_u64_compare);qsort(cpu,count,sizeof(*cpu),full_u64_compare);
 snprintf(path,sizeof(path),"%s/headroom.txt",dir);FILE *f=fopen(path,"w");if(!f)return;
 unsigned every=!failed&&pair_count==1200&&final.submitted==1200&&final.flipped==1200;
 fprintf(f,"suite=1.19-fullpaths1\nvariant=%s\nphysical=%d\nfailed=%d\nframeskip=0\nrows=%u\nwarmup_calls=120\nmeasured_calls=%u\nperiod_ns=16688154\ntarget_20_percent_ns=13350523\nservice_proxy=step_minus_verified_pure_pacing_wait_plus_all_worker_CPU_conservative_overlap\nobserver_costs=included_no_calibration_subtraction\nobserver_measured_ns=%llu\nsubmitted=%llu\nflipped=%llu\nevery_frame_completed=%u\ninvalid_accounting=%u\n",
 getenv("D35_FULL_VARIANT")?getenv("D35_FULL_VARIANT"):"fixture",!mock,failed,pair_count,count,(unsigned long long)observer,(unsigned long long)final.submitted,(unsigned long long)final.flipped,every,invalid);
 if(count)fprintf(f,"service_mean_ns=%llu\nservice_median_ns=%llu\nservice_p95_ns=%llu\nservice_p99_ns=%llu\nservice_max_ns=%llu\nmain_call_CPU_median_ns=%llu\nmain_call_CPU_p95_ns=%llu\nmain_call_CPU_p99_ns=%llu\ndeadline_overruns=%u\nmargin_overruns=%u\n",
 (unsigned long long)(sum/count),(unsigned long long)service[(count-1)/2],(unsigned long long)service[(count-1)*95/100],(unsigned long long)service[(count-1)*99/100],(unsigned long long)service[count-1],(unsigned long long)cpu[(count-1)/2],(unsigned long long)cpu[(count-1)*95/100],(unsigned long long)cpu[(count-1)*99/100],over,margin_over);
 fprintf(f,"sampled_warm_20_percent_headroom=%s\nproduction_gate_passed=0\nfull_effect_headroom=requires_matched_heavy_interval_and_recovery_analysis\n",
 mock?"NOT_PHYSICAL":failed||!every||invalid||!count?"INVALID_OR_INCOMPLETE":margin_over?"NOT_MET":"MET_IN_THIS_WARM_SAMPLE");
 fflush(f);fsync(fileno(f));fclose(f);
}
#endif
