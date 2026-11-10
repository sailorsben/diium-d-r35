"""Add exact display reuse to an isolated copy of the qualified cold runner."""
from importlib import import_module
from pathlib import Path
import shutil
import sys


replace_once = import_module('prepare-snes-throughput').replace_once


def prepare(source, destination):
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(
        '*.o', '*.log', 'mock', 'candidate', 'cases', 'plus-a7.so'))
    runner = destination/'runner'
    shutil.copyfile(Path(__file__).with_name('snes-rgb565-reuse.h'), runner/'snes-rgb565-reuse.h')

    board = runner/'board.c'
    text = board.read_text()
    text = replace_once(text, '#define SLOT_BYTES', '#include "snes-rgb565-reuse.h"\n\n#define SLOT_BYTES')
    text = replace_once(text, '    int reserved;\n', '    int reserved, previous, reuse_identical;\n')
    text = replace_once(text, '    unsigned audio_rate;', '    unsigned audio_rate;\n    bool measure_display;')
    text = replace_once(text, '    b.reserved=-1; b.queue_head=b.queue_count=0;',
                        '    b.reserved=b.previous=-1; b.reuse_identical=0; b.queue_head=b.queue_count=0;')
    free_slot = 'if(b.slots[slot].owner==FREE) break;'
    assert text.count(free_slot) == 2
    text = text.replace(free_slot, 'if(b.slots[slot].owner==FREE && (int)slot!=b.previous) break;')
    text = replace_once(text, 'int board_video_submit(const void *rgb565', '''/* Sole producer, at a session boundary. A retained slot may still be
 * READY or SCALER, and cannot be reserved even after scaler release. */
void board_video_reuse_identical(int enabled)
{
    pthread_mutex_lock(&display_lock);
    b.previous=-1;
    b.reuse_identical=enabled;
    pthread_cond_broadcast(&display_condition);
    pthread_mutex_unlock(&display_lock);
}

int board_video_submit(const void *rgb565''')
    text = replace_once(text, '    start=board_now_ns();\n    unsigned direct=', '''    int previous=b.previous;
    uint64_t comparison=0;
    if(previous>=0 && b.slots[previous].width==width && b.slots[previous].height==height) {
        uint64_t began=board_now_ns();
        bool same=d35_same_rgb565(rgb565,pitch,b.pixels+(unsigned)previous*SLOT_BYTES+32,width,height);
        comparison=board_now_ns()-began;
        if(same) {
            pthread_mutex_lock(&display_lock);
            b.metrics.compare_ns+=comparison;
            ++b.metrics.reused_identical;
            b.slots[slot].owner=FREE;
            b.reserved=-1;
            pthread_cond_broadcast(&display_condition);
            pthread_mutex_unlock(&display_lock);
            return 1; /* The last ordered presentation already contains these bytes. */
        }
    }
    start=board_now_ns();
    unsigned direct=''')
    text = replace_once(text, '    ++b.queue_count; ++b.metrics.submitted;',
                        '    b.metrics.compare_ns+=comparison;\n    if(b.reuse_identical) b.previous=(int)slot;\n    ++b.queue_count; ++b.metrics.submitted;')
    audio_start = text.index('int board_audio_open(unsigned requested_rate)\n{\n    int rate;')
    audio_end = text.index('void board_close(void)', audio_start)
    audio = text[audio_start:audio_end]
    audio = replace_once(audio, '    board_audio_close();\n    if(b.null_backend)',
                         '''    board_audio_close();
    const char *mode=getenv("D35_MEASURE_DISPLAY");
    b.measure_display=mode && !strcmp(mode,"1");
    if(b.measure_display) { b.audio_rate=44100; return 44100; }
    if(b.null_backend)''')
    # Reuse the software sink for the display-only measurement. Real GPIO,
    # chunk allocation, scaler, worker and flip still use the board backend.
    after_open = audio.index('ssize_t board_audio_write')
    audio = audio[:after_open]+audio[after_open:].replace('b.null_backend', '(b.null_backend||b.measure_display)')
    audio = replace_once(audio, '    return (b.null_backend||b.measure_display)?"mock":pcm_error();',
                         '    return b.measure_display?"measurement_sink":b.null_backend?"mock":pcm_error();')
    text = text[:audio_start]+audio+text[audio_end:]
    board.write_text(text, newline='\n')

    header = runner/'board.h'
    text = replace_once(header.read_text(), 'int board_video_submit(', '''/* Submit returns 1 for byte-identical reuse, 0 for a queued frame, or -1. */
void board_video_reuse_identical(int enabled);
int board_video_submit(''')
    text = replace_once(text, 'struct board_video_metrics {', '''struct board_video_metrics {
    uint64_t reused_identical, compare_ns;''')
    header.write_text(text, newline='\n')

    control = runner/'runner.c'
    text = control.read_text()
    text = replace_once(text, '    if(board_video_submit(data,w,h,pitch)<0) fail("Display submission failed: %s",board_last_error());\n    else ++s.videos;',
                        '''    int submitted=board_video_submit(data,w,h,pitch);
    if(submitted<0) fail("Display submission failed: %s",board_last_error());
    else if(!submitted) ++s.videos;''')
    text = replace_once(text, '    save_ready=false;pair_begin();presentation_burst_begin();', '''    value=getenv("D35_IDENTICAL_VIDEO_REUSE");
    board_video_reuse_identical(value && !strcmp(value,"1"));
    save_ready=false;pair_begin();presentation_burst_begin();''')
    text = replace_once(text, '    combined_cleanup_wall=board_now_ns()-combined_cleanup_began;', '''    combined_cleanup_wall=board_now_ns()-combined_cleanup_began;
    board_video_reuse_identical(0);''')
    text = replace_once(text, 'board_is_null()?"mock":"native_alsa"', '''board_is_null()?"mock":
      !strcmp(board_audio_error(),"measurement_sink")?"measurement_sink":"native_alsa"''')
    control.write_text(text, newline='\n')

    samples = runner/'pair-host.h'
    text = replace_once(samples.read_text(), ',load_cpu_ns\\n",f);',
                        ',load_cpu_ns,reused_identical,compare_ns\\n",f);')
    start = text.index('        fprintf(f,"%u,')
    end = text.index('    }\n    fflush', start)
    row = replace_once(text[start:end], '%llu\\n",', '%llu,%llu,%llu\\n",')
    row = replace_once(row, '(unsigned long long)r->load_cpu);', '''(unsigned long long)r->load_cpu,
            (unsigned long long)r->video.reused_identical,(unsigned long long)r->video.compare_ns);''')
    samples.write_text(text[:start]+row+text[end:], newline='\n')

    headroom = runner/'combined-headroom.h'
    text = replace_once(headroom.read_text(), 'final.submitted+pair_rows[1199].skipped',
                        'final.submitted+final.reused_identical+pair_rows[1199].skipped')
    text = replace_once(text, ' fprintf(f,"final_worker_counters_valid=', ''' fprintf(f,"reused_identical=%llu\\ncompare_ns=%llu\\n",
     (unsigned long long)final.reused_identical,(unsigned long long)final.compare_ns);
 fprintf(f,"native_pcm=%d\\n",!mock && strcmp(board_audio_error(),"measurement_sink")!=0);
 fprintf(f,"final_worker_counters_valid=''')
    headroom.write_text(text, newline='\n')


if __name__ == '__main__':
    prepare(*(Path(p).resolve() for p in sys.argv[1:]))
