"""Build an isolated explicit-start PCM probe over the returned LCD runner."""
from importlib import import_module
from pathlib import Path
import shutil
import sys


replace_once = import_module('prepare-snes-throughput').replace_once


def prepare(source, destination):
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(
        '*.o', '*.log', 'mock', 'candidate', 'cases', 'plus-a7.so', 'display-check'))
    runner = destination / 'runner'
    path = runner / 'native-pcm.c'
    text = path.read_text()
    text = replace_once(text, 'static struct { int fd,started,error;',
                        'static struct snd_pcm_sw_params probe_sw;\n'
                        'static struct { int fd,started,error;')
    text = replace_once(text, 'int pcm_open(unsigned requested)\n{', '''/* This driver's PREPARE rewrites runtime start and silence settings.
 * Program them afterward, including on resume. The only START is our own. */
static int pcm_prepare_explicit(struct snd_pcm_sw_params *sw)
{
    if (ioctl(pcm.fd, SNDRV_PCM_IOCTL_PREPARE, 0) < 0) return -1;
    if (ioctl(pcm.fd, SNDRV_PCM_IOCTL_SW_PARAMS, sw) < 0) return -1;
    if (sw->start_threshold != sw->boundary || sw->silence_threshold || sw->silence_size) {
        errno = EPROTO;
        return -1;
    }
    return 0;
}

int pcm_open(unsigned requested)
{''')
    text = replace_once(text, '    int version,last=EINVAL;', '''    const char *mode = getenv("D35_PCM_DIAGNOSTIC_RESERVE");
    bool long_reserve = mode && !strcmp(mode, "1");
    bool medium_reserve = mode && !strcmp(mode, "150");
    int version,last=EINVAL;''')
    text = replace_once(text, '#include <poll.h>', '#include <poll.h>\n#include <stdbool.h>')
    text = replace_once(text, '        unsigned prime=(rates[r]*64u+999u)/1000u;', '''        if (long_reserve && (rates[r] != 44100 || periods[p] != 512)) continue;
        if (medium_reserve && (rates[r] != 44100 || periods[p] != 128)) continue;
        unsigned ms = medium_reserve ? 150u : 64u;
        unsigned prime = long_reserve ? 24576u : (rates[r] * ms + 999u) / 1000u;''')
    text = replace_once(text, '            sw.start_threshold=prime; /* kernel may START inside WRITEI at this reserve */',
                        '            sw.start_threshold=sw.boundary;')
    a = text.index('            operation="SW_PARAMS";')
    b = text.index('            pcm.config.rate=', a)
    text = text[:a] + '''            operation="PREPARE/SW_PARAMS";
            if (pcm_prepare_explicit(&sw) < 0) goto failed;
            if (sw.stop_threshold!=size || sw.avail_min!=periods[p] ||
                sw.boundary<=size || sw.boundary>LONG_MAX) {
                operation="SW_PARAMS_READBACK"; errno=EPROTO; goto failed;
            }
            probe_sw=sw;
''' + text[b:]
    text = replace_once(text, 'if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_PREPARE,0)<0) return pcm_fail("PREPARE",errno);',
                        'if(pcm_prepare_explicit(&probe_sw)<0) return pcm_fail("PREPARE/SW_PARAMS",errno);')
    path.write_text(text, newline='\n')

    owner = runner / 'audio-owner.c'
    text = replace_once(owner.read_text(), '#define AUDIO_CAPACITY 8192u', '#define AUDIO_CAPACITY 32768u')
    owner.write_text(text, newline='\n')
    control = runner / 'runner.c'
    text = replace_once(control.read_text(), 'static const int16_t silence[4096*2]={0};',
                        'static const int16_t silence[24576*2]={0};')
    text = replace_once(text, '!frames || frames>4096 || audio_pipe_start()',
                        '!frames || frames>sizeof(silence)/sizeof(silence[0])/2 || audio_pipe_start()')
    anchor = '    if(!p_retro_load_game(&game)) { fail("Core rejected game"); goto done; }\n    s.loaded=true;'
    text = replace_once(text, anchor, anchor + '''
    const char *memo_mode = getenv("D35_AUDIT_MODE2_MEMO");
    if (memo_mode && !strcmp(memo_mode, "1")) {
        void (*set_memo)(bool) = NULL;
        *(void **)(&set_memo) = dlsym(s.core, "d35_raster_set_enabled");
        if (!set_memo) { fail("Core lacks audit raster toggle"); goto done; }
        set_memo(true);
    }''')
    control.write_text(text, newline='\n')


if __name__ == '__main__':
    prepare(*(Path(arg).resolve() for arg in sys.argv[1:]))
