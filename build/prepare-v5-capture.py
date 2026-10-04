from pathlib import Path

p=Path(__file__).resolve().parent
s=(p/'build-v4-diag.sh').read_text().replace('v4-diagnostic','v5-capture')
for old,new in [('emu_sfc_plus_v4_diag.c','emu_sfc_plus_v5_capture.c'),
                ('adapter-check-v4-diag.c','adapter-check-v5-capture.c'),
                ('video-contract-check-v4-diag.c','video-contract-check-v5-capture.c'),
                ('audio-diagnostics-check-v4.c','audio-diagnostics-check-v5.c'),
                ('harness-v4-diag.c','harness-v5-capture.c')]:
    s=s.replace(old,new)
(p/'build-v5-capture.sh').write_bytes(s.encode())
for old,new in [('adapter-check-v4-diag.c','adapter-check-v5-capture.c'),
                ('video-contract-check-v4-diag.c','video-contract-check-v5-capture.c')]:
    (p/new).write_text((p/old).read_text().replace('emu_sfc_plus_v4_diag.c','emu_sfc_plus_v5_capture.c'))
s=(p/'audio-diagnostics-check-v4.c').read_text().replace('#include "audio_diagnostics_v4.h"',
    '#include "device_audio_capture.h"\n#include "audio_diagnostics_v5_capture.h"')
s=s.replace('   diag_reset(); errno = EAGAIN;', '''   capture_reset();
   int16_t chunk[16];
   for (unsigned i=0; i<8; ++i) { chunk[2*i]=1234; chunk[2*i+1]=-1234; }
   capture_feed(chunk,8,1,0); assert(capture_count==0);
   for (unsigned i=0; capture_count<CAPTURE_FRAMES; ++i)
      capture_feed(chunk,8,8400+i,1000+(uint64_t)i*8);
   assert(__atomic_load_n(&capture_complete,__ATOMIC_ACQUIRE)==1);
   assert(capture_count==CAPTURE_FRAMES && capture_first_output_frame==1000);
   assert(captured_pcm[0]==1234 && captured_pcm[CAPTURE_FRAMES*2-1]==-1234);
   chunk[0]=9876; capture_feed(chunk,8,50000,999999);
   assert(capture_count==CAPTURE_FRAMES && captured_pcm[0]==1234);
   capture_reset(); /* Do not overwrite the FF3 test capture from this mock. */
   puts("PASS bounded capture starts at target run, completes exactly, and cannot overwrite completed PCM");
   diag_reset(); errno = EAGAIN;''')
(p/'audio-diagnostics-check-v5.c').write_text(s)
s=(p/'harness-v4-diag.c').read_text().replace('v4 diagnostic','v5 diagnostic')
s=s.replace('fclose(report);\n         puts', '''fclose(report);
         const char *directory=getenv("D35_CAPTURE_DIRECTORY");
         char name_buffer[1100]; assert(directory);
         snprintf(name_buffer,sizeof(name_buffer),"%s/emu_sfc_plus_v5_audio.wav",directory);
         FILE *capture=fopen(name_buffer,"rb"); assert(capture);
         unsigned char header[44]; assert(fread(header,1,44,capture)==44);
         assert(!memcmp(header,"RIFF",4) && !memcmp(header+8,"WAVEfmt ",8));
         fseek(capture,0,SEEK_END); assert(ftell(capture)==44+44100*6*4);
         fclose(capture);
         puts("PASS complete six-second WAV saved during play before unload");
         puts''')
(p/'harness-v5-capture.c').write_text(s)
s=(p/'run-v4-diag-checks.sh').read_text().replace('v4-diagnostic','v5-capture')
s=s.replace('export D35_TIMING_LOG=',
    'export D35_CAPTURE_START_RUN=300\nexport D35_CAPTURE_DIRECTORY="$base/v5-capture/verification"\nexport D35_TIMING_LOG=')
(p/'run-v5-capture-checks.sh').write_bytes(s.encode())
