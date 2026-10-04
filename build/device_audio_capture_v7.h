/* Sole producer and writer are the frontend thread. Feed only copies PCM;
 * Save state writes the latest six seconds while gameplay is paused.
 * The diagnostic worker never accesses this ring. */
#include <fcntl.h>
#include <unistd.h>
#define CAPTURE_FRAMES (44100u * 6u)
static int16_t captured_pcm[CAPTURE_FRAMES * 2u];
static uint32_t capture_count, capture_position, capture_last_run;
static uint64_t capture_first_output_frame;
static int capture_error;
static void capture_reset(void)
{
   capture_count=capture_position=capture_last_run=0;
   capture_first_output_frame=0; capture_error=0;
}
static void capture_feed(const int16_t *data, unsigned frames, uint32_t run, uint64_t first)
{
   unsigned remaining=frames;
   while (remaining) {
      unsigned n=CAPTURE_FRAMES-capture_position;
      if (n>remaining) n=remaining;
      memcpy(captured_pcm+capture_position*2,data,n*4);
      capture_position=(capture_position+n)%CAPTURE_FRAMES;
      capture_count = capture_count+n>CAPTURE_FRAMES ? CAPTURE_FRAMES : capture_count+n;
      data+=n*2; remaining-=n;
   }
   capture_last_run=run;
   capture_first_output_frame=first+frames-capture_count;
}
static void capture_u32(uint8_t *p,uint32_t n)
{ p[0]=n; p[1]=n>>8; p[2]=n>>16; p[3]=n>>24; }
static bool capture_sync_close(FILE *f)
{
   bool good=fflush(f)==0 && !ferror(f) && fsync(fileno(f))==0;
   if (fclose(f)) good=false;
   return good;
}
static bool capture_write(void)
{
   const char *directory=getenv("D35_CAPTURE_DIRECTORY");
   char path[1100],temporary[1100],metadata[1100];
   uint8_t header[44]={0}; FILE *f;
   unsigned start, first_part;
   capture_error=0;
   if (!capture_count) { capture_error=ENODATA; return false; }
   if (!directory) directory="/usr/retro";
   if (snprintf(path,sizeof(path),"%s/emu_sfc_plus_v7_audio.wav",directory)>=(int)sizeof(path) ||
       snprintf(temporary,sizeof(temporary),"%s.tmp",path)>=(int)sizeof(temporary) ||
       snprintf(metadata,sizeof(metadata),"%s/emu_sfc_plus_v7_capture.txt",directory)>=(int)sizeof(metadata)) {
      capture_error=ENAMETOOLONG; return false;
   }
   memcpy(header,"RIFF",4); capture_u32(header+4,36+capture_count*4);
   memcpy(header+8,"WAVEfmt ",8); capture_u32(header+16,16);
   header[20]=1; header[22]=2; capture_u32(header+24,44100);
   capture_u32(header+28,44100*4); header[32]=4; header[34]=16;
   memcpy(header+36,"data",4); capture_u32(header+40,capture_count*4);
   start=capture_count==CAPTURE_FRAMES ? capture_position : 0;
   first_part=CAPTURE_FRAMES-start;
   if (first_part>capture_count) first_part=capture_count;
   f=fopen(temporary,"wb"); if (!f) { capture_error=errno; return false; }
   if (fwrite(header,1,sizeof(header),f)!=sizeof(header) ||
       fwrite(captured_pcm+start*2,4,first_part,f)!=first_part ||
       fwrite(captured_pcm,4,capture_count-first_part,f)!=capture_count-first_part) {
      capture_error=errno ? errno : EIO; fclose(f); return false;
   }
   if (!capture_sync_close(f) || rename(temporary,path)) {
      capture_error=errno ? errno : EIO; return false;
   }
   f=fopen(metadata,"w"); if (!f) { capture_error=errno; return false; }
   fprintf(f,"Exact latest post-conversion PCM submitted to vendor frontend, saved on Save state.\n");
   fprintf(f,"rate=44100\nchannels=2\nbits=16\nframes=%u\nlast_run=%u\nfirst_output_frame=%llu\n",
      capture_count,capture_last_run,(unsigned long long)capture_first_output_frame);
   if (!capture_sync_close(f)) { capture_error=errno ? errno : EIO; return false; }
   int fd=open(directory,O_RDONLY|O_DIRECTORY);
   if (fd>=0) { (void)fsync(fd); close(fd); }
   return true;
}
