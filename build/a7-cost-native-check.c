/* Appended to the independent consuming provider, using the isolated real
 * runner/native client. This is a contract fixture, never A7 cost evidence. */
int main(int argc,char **argv)
{
    pthread_t consumer;struct audio_pipe_stats out;char dir[1200],path[1300];
    char *retained;size_t bytes;uint32_t hash;int rc;
    assert(argc==5);
    assert(!setenv("D35_COST_STATE",argv[3],1));
    assert(!setenv("D35_COST_MODE","0",1));
    assert(!setenv("D35_COST_CONTRACT_FIXTURE","1",1));
    assert(!pthread_create(&consumer,NULL,consume_pcm,NULL));next_menu=UINT_MAX;
    snprintf(dir,sizeof(dir),"%s/fault",argv[4]);assert(!mkdir(dir,0700));inject_write=1;
    assert(runner_run(argv[1],argv[2],dir)<0);
    audio_pipe_stats(&out);assert(out.error==EBADFD && out.epoch==1);
    assert(strstr(out.error_detail,"trace_synced=0"));
    snprintf(path,sizeof(path),"%s/pcm-full.txt",dir);
    retained=(char *)read_file(path,8*1024*1024,&bytes);assert(retained && bytes>100);
    retained=realloc(retained,bytes+1);assert(retained);retained[bytes]=0;
    assert(strstr(retained,"retained_from=0") && strstr(retained,"WRITEI_FRAMES errno=77"));
    hash=crc32(0,(unsigned char *)retained,(uInt)bytes);free(retained);
    assert(device_fd<0 && device_opens==1);
    snprintf(dir,sizeof(dir),"%s/retry",argv[4]);assert(!mkdir(dir,0700));inject_write=0;
    rc=runner_run(argv[1],argv[2],dir);if(rc)fprintf(stderr,"retry: %s\n",runner_last_error());assert(!rc);
    audio_pipe_stats(&out);assert(s.runs==120 && s.videos==120 && !s.held);
    assert(!out.errors && !out.remaining && !out.cleared && out.accepted==out.enqueued);
    assert(device_fd<0 && device_opens==2);
    snprintf(dir,sizeof(dir),"%s/deficit",argv[4]);assert(!mkdir(dir,0700));deficit_mode=1;
    assert(runner_run(argv[1],argv[2],dir)<0);
    audio_pipe_stats(&out);assert(out.error==EPIPE && out.xruns==1 && out.epoch==1);
    assert(s.runs<120 && !s.held && s.primed==2823 && out.accepted+out.remaining==out.enqueued);
    retained=(char *)read_file(path,8*1024*1024,&bytes);assert(retained);
    assert(crc32(0,(unsigned char *)retained,(uInt)bytes)==hash);free(retained);
    pthread_mutex_lock(&kernel_lock);consumer_stop=1;pthread_mutex_unlock(&kernel_lock);pthread_join(consumer,NULL);
    puts("PASS: consuming native provider; truthful EBADFD; deferred full PCM flush after join; clean120-frame retry and drain; sustained deficit fails without hidden reprime; earlier evidence preserved");
    return 0;
}
