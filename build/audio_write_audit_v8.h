/* Diagnostic transport: same exported driver write and PCM pointer/count,
 * bypassing the launcher's wrapper which discards write(2)'s result.
 * Exactly one call; no retries, padding, rate changes or second submission.
 * Statistics are owned by the frontend thread and saved only on Save state. */
static ssize_t (*audited_driver_write)(const void *, size_t);
static int *audited_dsp;
static uint64_t audited_calls, audited_requested, audited_accepted, audited_fallback;
static uint32_t audited_short, audited_zero, audited_errors, audited_unaligned;
static uint32_t audited_first_bad_run, audited_last_bad_run;
static int audited_last_errno;
static ssize_t audited_last_result;
static bool audited_resolved;
static void audit_reset(void)
{
   audited_driver_write=NULL; audited_dsp=NULL; audited_resolved=false;
   audited_calls=audited_requested=audited_accepted=audited_fallback=0;
   audited_short=audited_zero=audited_errors=audited_unaligned=0;
   audited_first_bad_run=audited_last_bad_run=0;
   audited_last_errno=0; audited_last_result=0;
}
static bool audit_deliver(const int16_t *pcm, unsigned frames, uint32_t run)
{
   size_t bytes=(size_t)frames*4;
   ssize_t result;
   int error, saved_errno=errno;
   if (!audited_resolved && display_driver) {
      *(void **)(&audited_driver_write)=dlsym(display_driver,"sound_driver_playframe");
      *(void **)(&audited_dsp)=dlsym(display_driver,"DSP");
      audited_resolved=true;
   }
   if (!audited_driver_write || !audited_dsp || *audited_dsp<0) {
      ++audited_fallback; errno=saved_errno; return false;
   }
   errno=0;
   result=audited_driver_write(pcm,bytes);
   error=result<0 ? errno : 0;
   ++audited_calls; audited_requested+=bytes;
   if (result>0) audited_accepted+=(uint64_t)result;
   if (result<0) ++audited_errors;
   else if (!result) ++audited_zero;
   else if ((size_t)result!=bytes) ++audited_short;
   if (result>0 && result%4) ++audited_unaligned;
   if (result<0 || (size_t)result!=bytes) {
      if (!audited_first_bad_run) audited_first_bad_run=run;
      audited_last_bad_run=run; audited_last_errno=error; audited_last_result=result;
   }
   errno=saved_errno;
   return true; /* Even a failed write was attempted. Never also call frontend. */
}
static bool audit_save(void)
{
   const char *directory=getenv("D35_CAPTURE_DIRECTORY");
   char path[1100], temporary[1100]; FILE *f;
   if (!directory) directory="/usr/retro";
   if (snprintf(path,sizeof(path),"%s/emu_sfc_plus_v8_write_audit.txt",directory)>=(int)sizeof(path) ||
       snprintf(temporary,sizeof(temporary),"%s.tmp",path)>=(int)sizeof(temporary)) return false;
   f=fopen(temporary,"w"); if (!f) return false;
   fprintf(f,"Driver sound_driver_playframe return values; exactly one driver call per callback, unchanged PCM.\n");
   fprintf(f,"driver_calls=%llu\nrequested_bytes=%llu\naccepted_bytes=%llu\nfrontend_fallback_calls=%llu\n",
      (unsigned long long)audited_calls,(unsigned long long)audited_requested,
      (unsigned long long)audited_accepted,(unsigned long long)audited_fallback);
   fprintf(f,"short_writes=%u\nzero_writes=%u\nwrite_errors=%u\nunaligned_results=%u\n",
      audited_short,audited_zero,audited_errors,audited_unaligned);
   fprintf(f,"first_bad_run=%u\nlast_bad_run=%u\nlast_bad_errno=%d\nlast_bad_result=%d\n",
      audited_first_bad_run,audited_last_bad_run,audited_last_errno,(int)audited_last_result);
   if (!capture_sync_close(f) || rename(temporary,path)) return false;
   int fd=open(directory,O_RDONLY|O_DIRECTORY);
   if (fd>=0) { (void)fsync(fd); close(fd); }
   return true;
}
