from pathlib import Path
import shutil
import json
from hashlib import sha256

base = Path(__file__).resolve().parent
evidence = base.parent / 'device-evidence/card-D-v5-return'
evidence.mkdir(exist_ok=False)
for name in ['emu_sfc_plus_v5.log', 'emu_sfc_plus_v5_audio.wav',
             'emu_sfc_plus_v5_capture.txt', 'emu_sfc_plus_v5_timing.log']:
    p = Path('D:/retro') / name
    if p.exists(): shutil.copy2(p, evidence / name)
shutil.copy2('D:/retro/libs/emu_sfc.so', evidence / 'emu_sfc.so')
(evidence / 'return.json').write_text(json.dumps({
    'adapter_sha256': sha256((evidence / 'emu_sfc.so').read_bytes()).hexdigest(),
    'missing': [n for n in ['emu_sfc_plus_v5_audio.wav', 'emu_sfc_plus_v5_capture.txt',
                           'emu_sfc_plus_v5_timing.log'] if not (evidence / n).exists()],
    'conclusion': 'Startup succeeded; no capture or periodic timing report returned. Cause unproven.'
}, indent=2))

names = ['emu_sfc_plus_v5_capture.c', 'audio_diagnostics_v5_capture.h',
         'build-v5-capture.sh', 'run-v5-capture-checks.sh',
         'adapter-check-v5-capture.c', 'video-contract-check-v5-capture.c',
         'harness-v5-capture.c', 'audio-diagnostics-check-v5.c']
for name in names:
    dest = name.replace('v5', 'v6')
    text = (base / name).read_text().replace('v5', 'v6')
    text = text.replace('"device_audio_capture.h"', '"device_audio_capture_v6.h"')
    if name == 'emu_sfc_plus_v5_capture.c':
        text = text.replace('   capture_write();\n', '')
        text = text.replace('{ diag_worker_stop(); diag_dump(); capture_write(); }',
                            '{ diag_worker_stop(); diag_dump(); }')
        text = text.replace('   bytes = (uint32_t)p_retro_serialize_size();',
            '   bool recorded = capture_write();\n'
            '   message("Save-state audio capture: saved=%d frames=%u last_run=%u first_output_frame=%llu error=%d\\n",\n'
            '      recorded, capture_count, capture_last_run,\n'
            '      (unsigned long long)capture_first_output_frame, capture_error);\n'
            '   bytes = (uint32_t)p_retro_serialize_size();')
    if name == 'audio_diagnostics_v5_capture.h':
        text = text.replace('      capture_write();\n', '')
    if name == 'harness-v5-capture.c':
        text = text.replace('         const char *directory=getenv("D35_CAPTURE_DIRECTORY");',
            '         size_t save_bytes=retro_serialize_size();\n'
            '         void *save=malloc(save_bytes); assert(save);\n'
            '         assert(retro_serialize(save,save_bytes)); free(save);\n'
            '         const char *directory=getenv("D35_CAPTURE_DIRECTORY");')
        text = text.replace('PASS complete six-second WAV saved during play before unload',
                            'PASS latest six-second WAV saved explicitly by Save state before unload')
    if name == 'audio-diagnostics-check-v5.c':
        start = text.index('   capture_reset();')
        end = text.index('   diag_reset(); errno', start)
        text = text[:start] + '''   capture_reset();
   int16_t chunk[16];
   uint64_t sent=0;
   for (unsigned block=0; block<34000; ++block) {
      for (unsigned i=0; i<8; ++i) {
         chunk[2*i]=(int16_t)(sent+i); chunk[2*i+1]=(int16_t)(-(int)(sent+i));
      }
      capture_feed(chunk,8,block+1,sent); sent+=8;
   }
   assert(capture_count==CAPTURE_FRAMES);
   assert(capture_first_output_frame==sent-CAPTURE_FRAMES);
   setenv("D35_CAPTURE_DIRECTORY",".",1);
   assert(capture_write());
   FILE *wav=fopen("emu_sfc_plus_v6_audio.wav","rb"); assert(wav);
   assert(!fseek(wav,44,SEEK_SET));
   for (uint64_t i=sent-CAPTURE_FRAMES; i<sent; ++i) {
      int16_t pair[2]; assert(fread(pair,4,1,wav)==1);
      assert(pair[0]==(int16_t)i && pair[1]==(int16_t)(-(int)i));
   }
   assert(fgetc(wav)==EOF); fclose(wav);
   capture_reset();
   capture_feed(chunk,8,1,0); assert(capture_count==8 && capture_write());
   setenv("D35_CAPTURE_DIRECTORY","/missing-d35-directory",1);
   assert(!capture_write() && capture_error!=0);
   capture_reset();
   puts("PASS rolling capture preserves exact latest samples across wrap; partial save and write errors verified");
''' + text[end:]
    (base / dest).write_text(text, newline='\n')
print('Preserved v5 return and prepared v6 test/build sources.')
