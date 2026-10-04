from pathlib import Path

p=Path(__file__).resolve().parent
s=(p/'build-v3-diag.sh').read_text().replace('v3','v4')
s=s.replace('audio-diagnostics-check.c','audio-diagnostics-check-v4.c')
s=s.replace('harness.c','harness-v4-diag.c')
s=s.replace('-l:libdl-2.30.so', '-l:libpthread-2.30.so -l:ld-2.30.so -l:libdl-2.30.so')
(p/'build-v4-diag.sh').write_bytes(s.encode())
for old,new in [('adapter-check-v3-diag.c','adapter-check-v4-diag.c'),
                ('video-contract-check-v3-diag.c','video-contract-check-v4-diag.c')]:
    (p/new).write_text((p/old).read_text().replace('v3','v4'))
s=(p/'audio-diagnostics-check.c').read_text().replace('audio_diagnostics.h','audio_diagnostics_v4.h')
s=s.replace('   puts("PASS diagnostic:', '''   /* Periodic output must happen without serialize, deinit or exit. */
   diag_reset(); queue_value=512;
   setenv("D35_DIAG_INTERVAL_MS","100",1);
   setenv("D35_TIMING_LOG","periodic-mock.log",1);
   int original_priority=getpriority(PRIO_PROCESS,0);
   diag_worker_start(); assert(!diag_worker_error);
   m=diag_audio_before(); diag_audio_after(m,30,736);
   bool found=false;
   for (unsigned i=0; i<100; ++i) {
      FILE *report=fopen("periodic-mock.log","r");
      if (report) { char line[512]; assert(fgets(line,sizeof(line),report)); fclose(report);
         if (strstr(line,"run=30;")) { found=true; break; } }
      usleep(10000);
   }
   assert(found && getpriority(PRIO_PROCESS,0)==original_priority);
   /* A busy snapshot lock drops measurements; it never blocks gameplay. */
   pthread_mutex_lock(&diag_mutex);
   uint64_t began=diag_now();
   diag_frame_done(30,began); diag_video_done(30,began);
   assert(diag_now()-began<10000);
   pthread_mutex_unlock(&diag_mutex);
   assert(__atomic_load_n(&diag_skipped,__ATOMIC_RELAXED)>=2);
   began=diag_now(); diag_worker_stop();
   assert(diag_now()-began<1000000);
   puts("PASS periodic report before exit/save; no gameplay wait; worker joins promptly");
   puts("PASS diagnostic:''')
(p/'audio-diagnostics-check-v4.c').write_text(s)
s=(p/'harness.c').read_text()
s=s.replace('for (run_number = 0; run_number < 1800; ++run_number) retro_run();', '''for (run_number = 0; run_number < 1800; ++run_number) {
      retro_run();
      if (run_number==899) {
         const char *name=getenv("D35_TIMING_LOG");
         FILE *report=name ? fopen(name,"r") : NULL;
         char line[512]; assert(report && fgets(line,sizeof(line),report));
         assert(strstr(line,"v4 diagnostic") && !strstr(line,"run=0;"));
         fclose(report);
         puts("PASS periodic FF3 timing log exists at frame 900, before serialization/unload");
      }
   }''')
(p/'harness-v4-diag.c').write_text(s)
s=(p/'run-v3-diag-checks.sh').read_text().replace('v3','v4')
s=s.replace('export D35_TIMING_LOG=', 'export D35_DIAG_INTERVAL_MS=100\nexport D35_TIMING_LOG=')
(p/'run-v4-diag-checks.sh').write_bytes(s.encode())
