/* One bounded, exact PCM capture. Sole producer is the gameplay thread.
 * Reporter reads only after an atomic release/acquire handoff of completion.
 * No file writes, locks, sample edits or waits occur in capture_feed(). */
#include <fcntl.h>
#include <unistd.h>
#define CAPTURE_FRAMES (44100u * 6u)
static int16_t captured_pcm[CAPTURE_FRAMES * 2u];
static uint32_t capture_count, capture_start_run = 8400, capture_first_run, capture_last_run;
static uint64_t capture_first_output_frame;
static unsigned capture_complete;
static bool capture_written;
static void capture_reset(void)
{
   const char *test=getenv("D35_CAPTURE_START_RUN");
   capture_count=capture_first_run=capture_last_run=0;
   capture_first_output_frame=0; capture_complete=0; capture_written=false;
   capture_start_run=8400;
   if (test) {
      const char *p=test; unsigned n=0;
      while (*p>='0' && *p<='9' && n<=1000000) { n=n*10+(unsigned)(*p-'0'); ++p; }
      if (!*p && n>0 && n<=1000000) capture_start_run=n;
   }
}
static void capture_feed(const int16_t *data, unsigned frames, uint32_t run, uint64_t first)
{
   unsigned n;
   if (capture_count==CAPTURE_FRAMES || run<capture_start_run) return;
   if (!capture_count) { capture_first_run=run; capture_first_output_frame=first; }
   n=frames;
   if (n>CAPTURE_FRAMES-capture_count) n=CAPTURE_FRAMES-capture_count;
   memcpy(captured_pcm+capture_count*2,data,n*4);
   capture_count+=n; capture_last_run=run;
   if (capture_count==CAPTURE_FRAMES) __atomic_store_n(&capture_complete,1,__ATOMIC_RELEASE);
}
static void capture_u32(uint8_t *p,uint32_t n)
{ p[0]=n; p[1]=n>>8; p[2]=n>>16; p[3]=n>>24; }
static bool capture_sync_close(FILE *f)
{
   bool good=fflush(f)==0 && !ferror(f) && fsync(fileno(f))==0;
   if (fclose(f)) good=false;
   return good;
}
static void capture_write(void)
{
   const char *directory=getenv("D35_CAPTURE_DIRECTORY");
   char path[1100],temporary[1100],metadata[1100];
   uint8_t header[44]={0}; FILE *f;
   if (!__atomic_load_n(&capture_complete,__ATOMIC_ACQUIRE) || capture_written) return;
   if (!directory) directory="/usr/retro";
   if (snprintf(path,sizeof(path),"%s/emu_sfc_plus_v5_audio.wav",directory)>=(int)sizeof(path) ||
       snprintf(temporary,sizeof(temporary),"%s.tmp",path)>=(int)sizeof(temporary) ||
       snprintf(metadata,sizeof(metadata),"%s/emu_sfc_plus_v5_capture.txt",directory)>=(int)sizeof(metadata)) return;
   memcpy(header,"RIFF",4); capture_u32(header+4,36+CAPTURE_FRAMES*4);
   memcpy(header+8,"WAVEfmt ",8); capture_u32(header+16,16);
   header[20]=1; header[22]=2; capture_u32(header+24,44100);
   capture_u32(header+28,44100*4); header[32]=4; header[34]=16;
   memcpy(header+36,"data",4); capture_u32(header+40,CAPTURE_FRAMES*4);
   f=fopen(temporary,"wb"); if (!f) return;
   if (fwrite(header,1,sizeof(header),f)!=sizeof(header) ||
       fwrite(captured_pcm,4,CAPTURE_FRAMES,f)!=CAPTURE_FRAMES) { fclose(f); return; }
   if (!capture_sync_close(f) || rename(temporary,path)) return;
   f=fopen(metadata,"w"); if (!f) return;
   fprintf(f,"Captured the exact post-conversion PCM passed to the vendor frontend; no inserted silence or skipped samples.\n");
   fprintf(f,"rate=44100\nchannels=2\nbits=16\nframes=%u\nfirst_run=%u\nlast_run=%u\nfirst_output_frame=%llu\n",
      CAPTURE_FRAMES,capture_first_run,capture_last_run,(unsigned long long)capture_first_output_frame);
   if (!capture_sync_close(f)) return;
   /* Flush newly created file names when the filesystem supports it. */
   int fd=open(directory,O_RDONLY|O_DIRECTORY);
   if (fd>=0) { (void)fsync(fd); close(fd); }
   capture_written=true;
}
