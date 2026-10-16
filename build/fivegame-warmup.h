/* Cold SuperFX boot replay before native PCM opens. No snapshot continuation. */
static void warm_video(const void *p,unsigned w,unsigned h,size_t pitch){(void)p;(void)w;(void)h;(void)pitch;}
static size_t warm_audio(const int16_t *p,size_t n){(void)p;return n;}
static void warm_sample(int16_t l,int16_t r){(void)l;(void)r;}
static int game_warmup(const char *dir){const char *name=getenv("D35_GAME_WARMUP");if(!name)return 0;FILE *f=fopen(name,"r");if(!f)return 0;unsigned count=0;char line[128];uint64_t began=board_now_ns(),cpu=thread_cpu_ns();
 p_retro_set_video_refresh(warm_video);p_retro_set_audio_sample_batch(warm_audio);p_retro_set_audio_sample(warm_sample);
 while(fgets(line,sizeof(line),f)){char *a=strtok(line," \r\n"),*b=strtok(NULL," \r\n");unsigned n=ability_number(a,10),bits=ability_number(b,16);if(!n||bits>65535||n>8656-count){fclose(f);return 0;}s.buttons=bits;for(unsigned i=0;i<n;i++){if(!(count%64)&&(stop_requested||(board_poll_input()&BOARD_MENU))){setenv("D35_PAIR_ABORT","1",1);fclose(f);return 0;}p_retro_run();count++;}}
 fclose(f);p_retro_set_video_refresh(video);p_retro_set_audio_sample_batch(audio_batch);p_retro_set_audio_sample(audio_sample);s.buttons=0;
 char path[1300];snprintf(path,sizeof(path),"%s/warmup.txt",dir);f=fopen(path,"w");if(!f)return 0;fprintf(f,"cold_boot_calls=%u\nwall_ns=%llu\nthread_CPU_ns=%llu\naudio_discarded_before_native_open=1\nphysical_display_warmup=0\n",count,(unsigned long long)(board_now_ns()-began),(unsigned long long)(thread_cpu_ns()-cpu));fflush(f);fsync(fileno(f));fclose(f);return count==8656;}
static void game_final_state(const char *dir){if(!s.loaded||s.failed)return;size_t n=p_retro_serialize_size();void *data=calloc(1,n);if(!data)return;if(p_retro_serialize(data,n)){char path[1300];snprintf(path,sizeof(path),"%s/end-state.bin",dir);(void)save_file(path,data,n);}free(data);}
