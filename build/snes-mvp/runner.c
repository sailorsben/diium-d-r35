#define _GNU_SOURCE
#include "runner.h"
#include "board.h"
#include "audio-pipe.h"
#include <libretro.h>
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <math.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#include <zlib.h>

#define OUT_RATE (s.output_rate?s.output_rate:44100u)
#define RING_FRAMES 8192u
#define ROM_LIMIT (8u * 1024u * 1024u)
#define ZIP_LIMIT (16u * 1024u * 1024u)
#define STATE_LIMIT (8u * 1024u * 1024u)
#define STATE_HEADER 40u
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))

/* Every native frame is rendered. One kernel-monotonic production clock;
 * independent PCM service and bounded device queues absorb brief jitter. */
static char error_text[256], status_text[256], initial_sram[1024];
static runner_menu_callback menu_cb;
static void *menu_userdata;
static volatile sig_atomic_t stop_requested;
static struct retro_system_av_info native_av;

#define CORE_FUNCTIONS(X) \
 X(void,retro_set_environment,(retro_environment_t)) \
 X(void,retro_set_video_refresh,(retro_video_refresh_t)) \
 X(void,retro_set_audio_sample,(retro_audio_sample_t)) \
 X(void,retro_set_audio_sample_batch,(retro_audio_sample_batch_t)) \
 X(void,retro_set_input_poll,(retro_input_poll_t)) \
 X(void,retro_set_input_state,(retro_input_state_t)) \
 X(unsigned,retro_api_version,(void)) \
 X(void,retro_init,(void)) X(void,retro_deinit,(void)) \
 X(void,retro_get_system_info,(struct retro_system_info *)) \
 X(void,retro_get_system_av_info,(struct retro_system_av_info *)) \
 X(void,retro_set_controller_port_device,(unsigned,unsigned)) \
 X(void,retro_reset,(void)) X(void,retro_run,(void)) \
 X(size_t,retro_serialize_size,(void)) \
 X(bool,retro_serialize,(void *,size_t)) \
 X(bool,retro_unserialize,(const void *,size_t)) \
 X(bool,retro_load_game,(const struct retro_game_info *)) \
 X(void,retro_unload_game,(void)) \
 X(void *,retro_get_memory_data,(unsigned)) \
 X(size_t,retro_get_memory_size,(unsigned))
#define DECLARE(type,name,args) static type (*p_##name) args;
CORE_FUNCTIONS(DECLARE)

static struct {
    void *core;
    bool initialized, loaded, failed, audio_open, audio_ready, pixel_format, state_unsafe;
    uint32_t buttons, rom_crc, core_crc, rom_bytes, core_bytes;
    unsigned input_rate, output_rate, phase, output_count, ring_count;
    bool have_previous, av_changed;
    int16_t previous[2], output[2048*2];
    char save_dir[1024], sram_path[1200], state_path[1200], report_path[1200];
    char progress_path[1200];
    uint64_t session_ns, next_progress, diagnostic_ns, diagnostic_max_ns;
    unsigned progress_writes, progress_errors;
    uint64_t runs, held, videos, video_dupes, generated, enqueued, accepted, primed;
    uint64_t write_calls, partial_writes, again, write_errors, pauses;
    uint64_t snapshot_loads,snapshot_rejections;
    uint64_t wall_ns, cpu_ns, video_ns, audio_ns, max_run_ns, max_video_ns;
    uint64_t start_ns, last_queue_sample;
    uint32_t run_hist[128], ring_high;
    int queue_min, queue_max;
    uint64_t audio_cleared, audio_remaining, audio_worker_cpu_ns, audio_max_gap_ns;
    uint64_t device_cleared_estimate, pacing_wait_ns, active_ns, late_calls, max_lateness_ns;
    uint64_t audio_space_wait_ns, audio_lead_wait_ns;
} s;
static void progress(const char *phase,int force);

static void fail(const char *fmt, ...)
{
    va_list ap;
    if (s.failed) return;
    va_start(ap,fmt); vsnprintf(error_text,sizeof(error_text),fmt,ap); va_end(ap);
    s.failed=true;
}
static void status(const char *fmt, ...)
{
    va_list ap;
    va_start(ap,fmt); vsnprintf(status_text,sizeof(status_text),fmt,ap); va_end(ap);
}
const char *runner_last_error(void) { return error_text; }
const char *runner_last_status(void) { return status_text; }
void runner_set_menu_callback(runner_menu_callback cb,void *userdata)
{ menu_cb=cb; menu_userdata=userdata; }
void runner_set_initial_sram(const char *path)
{ snprintf(initial_sram,sizeof(initial_sram),"%s",path?path:""); }
void runner_request_stop(void) { stop_requested=1; }

static uint32_t le32(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static unsigned le16(const uint8_t *p) { return p[0]|(unsigned)p[1]<<8; }
static void put32(uint8_t *p,uint32_t v)
{ unsigned i; for(i=0;i<4;i++) p[i]=(uint8_t)(v>>(i*8)); }

static void *read_file(const char *path,size_t limit,size_t *bytes)
{
    FILE *f=fopen(path,"rb"); long n; void *p;
    *bytes=0;
    if(!f) return NULL;
    if(fseek(f,0,SEEK_END)||(n=ftell(f))<0||(unsigned long)n>limit||fseek(f,0,SEEK_SET)) {
        fclose(f); errno=EINVAL; return NULL;
    }
    p=malloc(n?(size_t)n:1);
    if(!p) { fclose(f); return NULL; }
    if(fread(p,1,(size_t)n,f)!=(size_t)n) { free(p); fclose(f); errno=EIO; return NULL; }
    if(fclose(f)) { free(p); return NULL; }
    *bytes=(size_t)n; return p;
}
static bool fingerprint(const char *path,uint32_t *crc,uint32_t *bytes)
{
    uint8_t buf[16384]; size_t n; uint64_t total=0; uLong c=crc32(0,NULL,0);
    FILE *f=fopen(path,"rb");
    if(!f) return false;
    while((n=fread(buf,1,sizeof(buf),f))) { c=crc32(c,buf,(uInt)n); total+=n; }
    if(ferror(f)||total>UINT32_MAX) { fclose(f); return false; }
    if(fclose(f)) return false;
    *crc=(uint32_t)c; *bytes=(uint32_t)total; return true;
}
static bool ensure_directory(const char *path)
{
    char tmp[1024]; size_t i,n=strlen(path);
    if(!n||n>=sizeof(tmp)) return false;
    memcpy(tmp,path,n+1);
    for(i=1;i<=n;i++) if(tmp[i]=='/'||tmp[i]==0) {
        char c=tmp[i]; tmp[i]=0;
        if(mkdir(tmp,0755)&&errno!=EEXIST) return false;
        tmp[i]=c;
    }
    return true;
}

/* The private MVP namespace and previous generation are both preserved.
 * Verify temporary file contents before publishing. FAT32 is not power-loss
 * transactional, so .bak remains a recoverable previous generation. */
static bool save_file(const char *path,const void *data,size_t bytes)
{
    char temp[1280],backup[1280]; int fd=-1,dirfd; bool ok=false; size_t off=0,n;
    uint8_t *verify=NULL; uint32_t expected=(uint32_t)crc32(0,data,(uInt)bytes);
    if(snprintf(temp,sizeof(temp),"%s.tmp",path)>=(int)sizeof(temp)||
       snprintf(backup,sizeof(backup),"%s.bak",path)>=(int)sizeof(backup)) return false;
    fd=open(temp,O_WRONLY|O_CREAT|O_TRUNC,0644);
    if(fd<0) goto done;
    while(off<bytes) {
        ssize_t wrote=write(fd,(const uint8_t *)data+off,bytes-off);
        if(wrote<0&&errno==EINTR) continue;
        if(wrote<=0) goto done;
        off+=(size_t)wrote;
    }
    if(fsync(fd)) goto done;
    if(close(fd)) { fd=-1; goto done; } fd=-1;
    verify=read_file(temp,bytes,&n);
    if(!verify||n!=bytes||(uint32_t)crc32(0,verify,(uInt)n)!=expected) goto done;
    if(rename(path,backup)&&errno!=ENOENT) goto done;
    if(rename(temp,path)) { (void)rename(backup,path); goto done; }
    dirfd=open(s.save_dir,O_RDONLY|O_DIRECTORY);
    if(dirfd>=0) { (void)fsync(dirfd); close(dirfd); }
    ok=true;
done:
    if(fd>=0) close(fd);
    free(verify);
    if(!ok) (void)unlink(temp);
    return ok;
}

static bool snes_name(const uint8_t *p,unsigned len)
{
    char ext[5]; unsigned i;
    if(len<4||p[len-4]!='.') return false;
    for(i=0;i<4;i++) { char c=(char)p[len-4+i]; ext[i]=c>='A'&&c<='Z'?c+32:c; }
    ext[4]=0;
    return !strcmp(ext,".smc")||!strcmp(ext,".sfc")||!strcmp(ext,".fig")||!strcmp(ext,".swc");
}
/* ZIP reader retained from v11: stored/deflated, nonencrypted SNES payload. */
static void *unzip(const uint8_t *zip,size_t bytes,size_t *rom_bytes)
{
    size_t end,cd,limit; unsigned count,i;
    if(bytes<22) return NULL;
    limit=bytes>65557?bytes-65557:0; end=bytes-22;
    while(le32(zip+end)!=0x06054b50||end+22+le16(zip+end+20)!=bytes) {
        if(end==limit) return NULL;
        --end;
    }
    if(le16(zip+end+4)||le16(zip+end+6)) return NULL;
    count=le16(zip+end+10); cd=le32(zip+end+16);
    if(cd>end||le32(zip+end+12)>end-cd) return NULL;
    for(i=0;i<count;i++) {
        size_t next,local,start; unsigned names,method;
        uint32_t packed,unpacked,crc; void *result;
        if(cd>end||end-cd<46||le32(zip+cd)!=0x02014b50) return NULL;
        names=le16(zip+cd+28); next=cd+46+names+le16(zip+cd+30)+le16(zip+cd+32);
        if(next>end) return NULL;
        if(!snes_name(zip+cd+46,names)) { cd=next; continue; }
        if(le16(zip+cd+8)&1) return NULL;
        method=le16(zip+cd+10); crc=le32(zip+cd+16);
        packed=le32(zip+cd+20); unpacked=le32(zip+cd+24); local=le32(zip+cd+42);
        if(!unpacked||unpacked>ROM_LIMIT||local>bytes||bytes-local<30||le32(zip+local)!=0x04034b50) return NULL;
        start=local+30+le16(zip+local+26)+le16(zip+local+28);
        if(start>bytes||packed>bytes-start) return NULL;
        result=malloc(unpacked); if(!result) return NULL;
        if(method==0&&packed==unpacked) memcpy(result,zip+start,unpacked);
        else if(method==8) {
            z_stream z; int rc;
            memset(&z,0,sizeof(z)); z.next_in=(Bytef *)(zip+start); z.avail_in=packed;
            z.next_out=result; z.avail_out=unpacked;
            if(inflateInit2(&z,-MAX_WBITS)!=Z_OK) { free(result); return NULL; }
            rc=inflate(&z,Z_FINISH); inflateEnd(&z);
            if(rc!=Z_STREAM_END||z.total_in!=packed||z.total_out!=unpacked) { free(result); return NULL; }
        } else { free(result); return NULL; }
        if((uint32_t)crc32(0,result,unpacked)!=crc) { free(result); return NULL; }
        *rom_bytes=unpacked; return result;
    }
    return NULL;
}

static void audio_reset(void)
{
    audio_pipe_clear();
    s.phase=s.output_count=s.ring_count=0; s.have_previous=false;
}
static void pump_audio(void)
{
    struct audio_pipe_stats stats;
    audio_pipe_stats(&stats);
    s.accepted=stats.accepted; s.write_calls=stats.writes; s.partial_writes=stats.partial;
    s.again=stats.again; s.write_errors=stats.errors; s.ring_high=stats.high;
    s.ring_count=stats.remaining; s.audio_remaining=stats.remaining;
    s.audio_cleared=stats.cleared; s.audio_worker_cpu_ns=stats.worker_cpu_ns;
    s.audio_max_gap_ns=stats.max_write_gap_ns;
    if(stats.observed_ns) {
        if(s.queue_min<0 || (int)stats.playable<s.queue_min) s.queue_min=(int)stats.playable;
        if((int)stats.playable>s.queue_max) s.queue_max=(int)stats.playable;
    }
    if(stats.error) fail("Audio service failed: %s",strerror(stats.error));
}
static bool prime_audio(void)
{
    /* Wait for actual PCM transfer and successful START before emulation. */
    static const int16_t silence[4096*2]={0};
    unsigned frames=audio_pipe_prime_frames();
    if(s.output_count) { fail("Audio priming requires an empty queue"); return false; }
    if(!frames || frames>4096 || audio_pipe_start()<0 ||
       audio_pipe_push(silence,frames)<0 || audio_pipe_primed()<0) {
        fail("Audio service startup failed: %s",strerror(errno)); return false;
    }
    s.primed+=frames;
    pump_audio(); return !s.failed;
}
static bool audio_flush(void)
{
    if(!s.output_count) return !s.failed;
    if(audio_pipe_push(s.output,s.output_count)<0) {
        int saved=errno;
        if(saved==ENOBUFS) fail("Audio software queue full; playback stopped");
        else fail("Audio publication failed: %s",strerror(saved));
        s.output_count=0; return false;
    }
    s.enqueued+=s.output_count;
    s.output_count=0; return !s.failed;
}
static size_t audio_batch(const int16_t *data,size_t frames)
{
    size_t i; uint64_t began=board_now_ns();
    if(!data||s.failed||!s.audio_ready) return 0;
    s.generated+=frames;
    if(s.input_rate==OUT_RATE) {
        if(audio_pipe_push(data,frames)<0) { fail("Native PCM publication: %s",strerror(errno)); return 0; }
        s.enqueued+=frames; s.audio_ns+=board_now_ns()-began; return frames;
    }
    for(i=0;i<frames&&!s.failed;i++) {
        const int16_t *now=data+i*2;
        if(!s.have_previous) {
            s.previous[0]=now[0]; s.previous[1]=now[1]; s.have_previous=true; continue;
        }
        while(s.phase<OUT_RATE) {
            unsigned ch;
            for(ch=0;ch<2;ch++) s.output[s.output_count*2+ch]=
                ((int32_t)s.previous[ch]*(int32_t)(OUT_RATE-s.phase)+
                 (int32_t)now[ch]*(int32_t)s.phase)/(int32_t)OUT_RATE;
            ++s.output_count; s.phase+=s.input_rate;
            if(s.output_count==2048&&!audio_flush()) break;
        }
        if(s.failed) break;
        s.phase-=OUT_RATE; s.previous[0]=now[0]; s.previous[1]=now[1];
    }
    (void)audio_flush(); s.audio_ns+=board_now_ns()-began;
    return s.failed?i:frames;
}
static void audio_sample(int16_t l,int16_t r)
{ int16_t data[2]={l,r}; (void)audio_batch(data,1); }
static void video(const void *data,unsigned w,unsigned h,size_t pitch)
{
    uint64_t began,end;
    if(s.failed) return;
    if(!data) { ++s.video_dupes; board_video_cancel(); fail("Core omitted a drawing in full-render mode"); return; }
    if(!w||!h||w>512||h>512||pitch<(size_t)w*2) {
        fail("Unsupported SNES video geometry %ux%u",w,h); return;
    }
    began=board_now_ns();
    if(board_video_submit(data,w,h,pitch)<0) fail("Display submission failed: %s",board_last_error());
    else ++s.videos;
    end=board_now_ns()-began; s.video_ns+=end;
    if(s.max_video_ns<end) s.max_video_ns=end;
}
static void input_poll(void) { /* Runner already captured one fresh GPIO snapshot. */ }
static int16_t input_state(unsigned port,unsigned device,unsigned index,unsigned id)
{
    (void)index;
    if(port||device!=RETRO_DEVICE_JOYPAD) return 0;
    if(id==RETRO_DEVICE_ID_JOYPAD_MASK) return (int16_t)(s.buttons&0xffff);
    return id<16?(int16_t)((s.buttons>>id)&1u):0;
}
static void core_log(enum retro_log_level level,const char *fmt,...)
{ (void)level; (void)fmt; /* No runtime console/SD logging in callbacks. */ }
static bool valid_av(const struct retro_system_av_info *av)
{
    return isfinite(av->timing.fps)&&av->timing.fps>=40&&av->timing.fps<=70&&
        isfinite(av->timing.sample_rate)&&av->timing.sample_rate>=8000&&av->timing.sample_rate<=96000&&
        av->geometry.base_width&&av->geometry.base_height&&
        av->geometry.base_width<=av->geometry.max_width&&av->geometry.base_height<=av->geometry.max_height&&
        av->geometry.max_width<=512&&av->geometry.max_height<=512;
}
static bool environment(unsigned cmd,void *data)
{
    switch(cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
        if(!data||*(enum retro_pixel_format *)data!=RETRO_PIXEL_FORMAT_RGB565) return false;
        s.pixel_format=true; return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE:
        if(!data) return false;
        *(bool *)data=true; return true;
    case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS: return true;
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
        if(!data) return false;
        ((struct retro_log_callback *)data)->log=core_log; return true;
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
        if(!data) return false;
        *(unsigned *)data=0; return true;
    case RETRO_ENVIRONMENT_SET_VARIABLES:
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS: return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE:
        if(!data) return false;
        ((struct retro_variable *)data)->value=NULL; return false;
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
        if(!data) return false;
        *(bool *)data=false; return true;
    case RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE:
        if(data) *(int *)data=3;
        return true;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
        if(!data) return false;
        *(const char **)data=s.save_dir; return true;
    case RETRO_ENVIRONMENT_SET_GEOMETRY: {
        const struct retro_game_geometry *g=data;
        if(!g||!g->base_width||!g->base_height||g->base_width>512||g->base_height>512) return false;
        native_av.geometry.base_width=g->base_width; native_av.geometry.base_height=g->base_height;
        native_av.geometry.aspect_ratio=g->aspect_ratio; return true;
    }
    case RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO: {
        const struct retro_system_av_info *av=data;
        if(!av||!valid_av(av)) return false;
        /* Live sink reconfiguration is outside the SNES MVP contract. Reject
         * unsupported changes honestly rather than corrupting same-run PCM. */
        if(s.loaded&&(av->timing.sample_rate!=native_av.timing.sample_rate||
                      av->timing.fps!=native_av.timing.fps)) return false;
        native_av=*av; return true;
    }
    case RETRO_ENVIRONMENT_SHUTDOWN: stop_requested=1; return true;
    default: return false;
    }
}

static bool load_sram(void)
{
    size_t n=0,expected=p_retro_get_memory_size(RETRO_MEMORY_SAVE_RAM); void *data;
    void *dest=p_retro_get_memory_data(RETRO_MEMORY_SAVE_RAM);
    if(!expected) return true;
    if(!dest||expected>ROM_LIMIT) { fail("Invalid SRAM memory contract"); return false; }
    errno=0; data=read_file(s.sram_path,expected,&n);
    if(!data&&errno==ENOENT&&initial_sram[0]) data=read_file(initial_sram,expected,&n);
    if(!data) {
        if(errno==ENOENT&&!initial_sram[0]) return true;
        fail("Could not read private/copied in-game save: %s",strerror(errno)); return false;
    }
    if(n!=expected) { free(data); fail("In-game save size differs (%u expected)",(unsigned)expected); return false; }
    memcpy(dest,data,expected); free(data); return true;
}
static bool save_sram(void)
{
    size_t n=p_retro_get_memory_size(RETRO_MEMORY_SAVE_RAM);
    void *data=p_retro_get_memory_data(RETRO_MEMORY_SAVE_RAM);
    if(!n) return true;
    if(!data||n>ROM_LIMIT||!save_file(s.sram_path,data,n)) {
        status("In-game save failed; previous generation retained"); return false;
    }
    return true;
}
static bool save_state(void)
{
    size_t n=p_retro_serialize_size(); uint8_t *p; bool ok=false;
    if(!n||n>STATE_LIMIT) { status("Core snapshot size is unsupported"); return false; }
    p=calloc(1,n+STATE_HEADER); if(!p) { status("Not enough memory for snapshot"); return false; }
    memcpy(p,"D35MVP01",8); put32(p+8,1); put32(p+12,s.rom_crc); put32(p+16,s.rom_bytes);
    put32(p+20,s.core_crc); put32(p+24,s.core_bytes); put32(p+28,(uint32_t)n);
    if(p_retro_serialize(p+STATE_HEADER,n)) {
        put32(p+32,(uint32_t)crc32(0,p+STATE_HEADER,(uInt)n));
        ok=save_file(s.state_path,p,n+STATE_HEADER);
    }
    free(p); status(ok?"Snapshot saved":"Snapshot save failed; previous generation retained"); return ok;
}
static bool load_state(void)
{
    size_t n; uint8_t *p=read_file(s.state_path,STATE_LIMIT+STATE_HEADER,&n);
    uint8_t *backup=NULL; bool ok=false;
    if(p&&n>=STATE_HEADER&&!memcmp(p,"D35MVP01",8)&&le32(p+8)==1&&
       le32(p+12)==s.rom_crc&&le32(p+16)==s.rom_bytes&&le32(p+20)==s.core_crc&&
       le32(p+24)==s.core_bytes&&le32(p+28)==n-STATE_HEADER&&
       n-STATE_HEADER==p_retro_serialize_size()&&
       le32(p+32)==(uint32_t)crc32(0,p+STATE_HEADER,(uInt)(n-STATE_HEADER))) {
        /* A core can mutate memory before rejecting a state. Preserve the live
         * game too, not just the snapshot files. */
        backup=malloc(n-STATE_HEADER);
        if(backup&&p_retro_serialize(backup,n-STATE_HEADER)) {
            ok=p_retro_unserialize(p+STATE_HEADER,n-STATE_HEADER);
            if(!ok&&!p_retro_unserialize(backup,n-STATE_HEADER)) {
                s.state_unsafe=true;
                fail("Snapshot failed and live-state recovery failed; restart the game");
            }
        }
    }
    free(backup);
    free(p); status(ok?"Snapshot loaded":"Snapshot missing, damaged or from a different core/ROM");
    if(ok) ++s.snapshot_loads; else ++s.snapshot_rejections;
    if(ok) audio_reset();
    return ok;
}

static bool pause_menu(void)
{
    int action;
    ++s.pauses; progress("pause_draining",1); board_wait_display();
    audio_pipe_stop(1); pump_audio();
    if(s.failed) return false;
    audio_reset();
    { int queued=board_audio_queued_frames(); if(queued>0) s.device_cleared_estimate+=(unsigned)queued; }
    if(board_audio_reset()<0) { fail("Could not pause audio: %s",board_last_error()); return false; }
    if(!save_sram()) { /* Show the error; don't claim the save succeeded. */ }
    else status("Paused");
    if(!menu_cb) return false;
    do {
        action=menu_cb(menu_userdata,status_text);
        if(action==RUNNER_SAVE_STATE) (void)save_state();
        else if(action==RUNNER_LOAD_STATE) {
            progress("snapshot_loading",1); (void)load_state(); progress("snapshot_loaded_or_rejected",1);
        }
        else if(action==RUNNER_RESET) { p_retro_reset(); audio_reset(); status("Game reset"); }
    } while(action!=RUNNER_RESUME&&action!=RUNNER_EXIT&&!stop_requested&&!s.failed);
    if(action==RUNNER_EXIT||stop_requested||s.failed) return false;
    audio_reset();
    return prime_audio();
}

static uint64_t thread_cpu_ns(void)
{
    struct timespec t;
    if(syscall(SYS_clock_gettime,CLOCK_THREAD_CPUTIME_ID,&t)) return 0;
    return (uint64_t)t.tv_sec*1000000000u+(uint64_t)t.tv_nsec;
}
static void report_to(const char *path,const char *phase,int ram)
{
    char text[6144]; int n; unsigned i;
    struct board_video_metrics display;
    board_video_metrics(&display,0);
    n=snprintf(text,sizeof(text),
      "D35 SNES MVP\nrom_crc32=%08x\nrom_bytes=%u\ncore_crc32=%08x\ncore_bytes=%u\n"
      "fps=%.9f\nnative_rate=%u\nsink_rate=%u\npacing=native_pcm_consumption_full_render\n"
      "mock_backend=%d\nruns=%llu\nheld=%llu\nvideo_submitted=%llu\nvideo_dupes=%llu\n"
      "native_audio_frames=%llu\nresampled_enqueued_frames=%llu\noutput_accepted_frames_including_priming=%llu\n"
      "priming_silence_frames=%llu\n"
      "write_calls=%llu\nshort_writes=%llu\neagain_or_zero=%llu\nwrite_errors=%llu\n"
      "software_ring_high_frames=%u\ndevice_queue_min_frames=%d\ndevice_queue_max_frames=%d\n"
      "core_wall_ns=%llu\ncore_thread_cpu_ns=%llu\nvideo_callback_ns=%llu\naudio_callback_ns=%llu\n"
      "max_run_ns=%llu\nmax_video_ns=%llu\npauses=%llu\nsnapshot_load_successes=%llu\nsnapshot_load_rejections=%llu\n"
      "present_count=unavailable_vendor_driver\nerror=%s\n",
      s.rom_crc,s.rom_bytes,s.core_crc,s.core_bytes,native_av.timing.fps,s.input_rate,OUT_RATE,
      board_is_null(),(unsigned long long)s.runs,(unsigned long long)s.held,
      (unsigned long long)s.videos,(unsigned long long)s.video_dupes,
      (unsigned long long)s.generated,(unsigned long long)s.enqueued,(unsigned long long)s.accepted,(unsigned long long)s.primed,
      (unsigned long long)s.write_calls,(unsigned long long)s.partial_writes,(unsigned long long)s.again,
      (unsigned long long)s.write_errors,s.ring_high,s.queue_min,s.queue_max,
      (unsigned long long)s.wall_ns,(unsigned long long)s.cpu_ns,(unsigned long long)s.video_ns,
      (unsigned long long)s.audio_ns,(unsigned long long)s.max_run_ns,(unsigned long long)s.max_video_ns,
      (unsigned long long)s.pauses,(unsigned long long)s.snapshot_loads,
      (unsigned long long)s.snapshot_rejections,error_text);
    if(n<=0||(size_t)n>=sizeof(text)) return;
    n+=snprintf(text+n,sizeof(text)-(size_t)n,
      "build_version=1.13\nsession_id=%ld-%llu\nphase=%s\ncheckpoint_kernel_ns=%llu\n"
      "session_elapsed_ns=%llu\naudio_space_wait_ns=%llu\naudio_lead_wait_ns=%llu\n"
      "diagnostic_ram_write_ns=%llu\nmax_diagnostic_ram_write_ns=%llu\n"
      "diagnostic_ram_writes=%u\ndiagnostic_ram_errors=%u\n",
      (long)getpid(),(unsigned long long)s.session_ns,phase,
      (unsigned long long)board_now_ns(),(unsigned long long)(board_now_ns()-s.session_ns),
      (unsigned long long)s.audio_space_wait_ns,(unsigned long long)s.audio_lead_wait_ns,
      (unsigned long long)s.diagnostic_ns,(unsigned long long)s.diagnostic_max_ns,
      s.progress_writes,s.progress_errors);
    if(n<=0||(size_t)n>=sizeof(text)) return;
    n+=snprintf(text+n,sizeof(text)-(size_t)n,
      "audio_cleared_frames=%llu\naudio_remaining_frames=%llu\naudio_worker_cpu_ns=%llu\n"
      "audio_max_write_gap_ns=%llu\ndevice_cleared_frames_estimate=%llu\n"
      "display_scaled=%llu\ndisplay_flipped=%llu\ndisplay_queue_high=%u\n"
      "display_reserve_wait_ns=%llu\ndisplay_copy_ns=%llu\nscaler_wall_ns=%llu\nflip_wall_ns=%llu\n"
      "display_worker_cpu_ns=%llu\nmax_scaler_ns=%llu\nmax_flip_ns=%llu\n"
      "active_wall_ns=%llu\npacing_wait_ns=%llu\nlate_calls=%llu\nmax_lateness_ns=%llu\n",
      (unsigned long long)s.audio_cleared,(unsigned long long)s.audio_remaining,
      (unsigned long long)s.audio_worker_cpu_ns,(unsigned long long)s.audio_max_gap_ns,
      (unsigned long long)s.device_cleared_estimate,
      (unsigned long long)display.scaled,(unsigned long long)display.flipped,display.queue_high,
      (unsigned long long)display.reserve_wait_ns,(unsigned long long)display.copy_ns,
      (unsigned long long)display.scale_ns,(unsigned long long)display.flip_ns,
      (unsigned long long)display.worker_cpu_ns,(unsigned long long)display.max_scale_ns,
      (unsigned long long)display.max_flip_ns,(unsigned long long)s.active_ns,
      (unsigned long long)s.pacing_wait_ns,(unsigned long long)s.late_calls,
      (unsigned long long)s.max_lateness_ns);
    if(n<=0||(size_t)n>=sizeof(text)) return;
    {
        struct audio_pipe_stats pcm;
        audio_pipe_stats(&pcm);
        n+=snprintf(text+n,sizeof(text)-(size_t)n,
          "audio_backend=%s\npcm_period_frames=%u\npcm_buffer_frames=%u\npcm_prime_frames=%u\n"
          "pcm_playable_frames=%u\npcm_state=%u\nxrun_count=%llu\npcm_observed_kernel_ns=%llu\n"
          "pcm_event_wakes=%llu\npcm_fault_poll_timeouts=%llu\n"
          "pcm_playable_min_running_frames=%d\npcm_playable_max_running_frames=%u\n"
          "pcm_admissions=%llu\npcm_admission_min_lead_frames=%d\npcm_admission_max_lead_frames=%u\n"
          "pcm_boundary_frames=%u\npcm_epoch=%u\npcm_epoch_transferred_frames=%llu\n"
          "pcm_avail_frames=%u\npcm_appl_ptr=%u\npcm_hw_ptr=%u\npcm_start_threshold=%u\n"
          "pcm_prime_transferred_frames=%u\npcm_start_calls=%u\npcm_start_races=%u\npcm_error_detail=%s\n",
          board_is_null()?"mock":"native_alsa",pcm.period,pcm.buffer,pcm.prime,pcm.playable,pcm.state,
          (unsigned long long)pcm.xruns,(unsigned long long)pcm.observed_ns,
          (unsigned long long)pcm.wakes,(unsigned long long)pcm.poll_timeouts,
          pcm.playable_min==UINT_MAX?-1:(int)pcm.playable_min,pcm.playable_max,
          (unsigned long long)pcm.admissions,pcm.admission_min==UINT_MAX?-1:(int)pcm.admission_min,pcm.admission_max,
          pcm.boundary,pcm.epoch,(unsigned long long)pcm.epoch_transferred,
          pcm.avail,pcm.appl_ptr,pcm.hw_ptr,pcm.start_threshold,pcm.prime_transferred,
          pcm.start_calls,pcm.start_races,pcm.error_detail);
    }
    if(n<=0||(size_t)n>=sizeof(text)) return;
    for(i=0;i<ARRAY_SIZE(s.run_hist);i++) if(s.run_hist[i]) {
        int add=snprintf(text+n,sizeof(text)-(size_t)n,"core_wall_bin_%ums=%u\n",i,s.run_hist[i]);
        if(add<0||(size_t)add>=sizeof(text)-(size_t)n) break;
        n+=add;
    }
    if(ram) {
        char temporary[1280]; int fd; size_t off=0;
        if(snprintf(temporary,sizeof(temporary),"%s.tmp",path)>=(int)sizeof(temporary)) return;
        fd=open(temporary,O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC,0600);
        if(fd<0) { ++s.progress_errors; return; }
        while(off<(size_t)n) {
            ssize_t wrote=write(fd,text+off,(size_t)n-off);
            if(wrote<0 && errno==EINTR) continue;
            if(wrote<=0) break;
            off+=(size_t)wrote;
        }
        if(close(fd) || off!=(size_t)n || rename(temporary,path)) ++s.progress_errors;
        else ++s.progress_writes;
    } else (void)save_file(path,text,(size_t)n);
}
static void progress(const char *phase,int force)
{
    uint64_t began=board_now_ns(),duration;
    if(!s.progress_path[0] || (!force && began<s.next_progress)) return;
    s.next_progress=began+1000000000u;
    pump_audio(); s.audio_worker_cpu_ns=audio_pipe_live_cpu();
    report_to(s.progress_path,phase,1);
    duration=board_now_ns()-began; s.diagnostic_ns+=duration;
    if(duration>s.diagnostic_max_ns) s.diagnostic_max_ns=duration;
}
static void report(void) { report_to(s.report_path,"finished",0); }

int runner_run(const char *rom_path,const char *core_path,const char *save_dir)
{
    void *file_data=NULL,*rom_data=NULL; size_t file_bytes=0,rom_bytes=0;
    struct retro_game_info game; struct retro_system_info info;
    uint64_t deadline=0,period=0,limit=0; double fraction=0,remainder=0;
    uint32_t old_buttons=0; bool no_pacing=false,save_ready=false;
    const char *value; int actual_rate;
    memset(&s,0,sizeof(s)); memset(&native_av,0,sizeof(native_av));
    s.session_ns=board_now_ns();
    value=getenv("D35_MVP_PROGRESS_FILE");
    if(value && *value && strlen(value)<sizeof(s.progress_path))
        strcpy(s.progress_path,value);
    audio_pipe_init(); board_video_metrics(NULL,1);
    error_text[0]=status_text[0]=0; stop_requested=0; s.queue_min=-1;s.queue_max=-1;
    if(!rom_path||!core_path||!save_dir||strlen(save_dir)>=sizeof(s.save_dir)) {
        fail("Invalid game/core/save path"); goto done;
    }
    snprintf(s.save_dir,sizeof(s.save_dir),"%s",save_dir);
    if(!ensure_directory(save_dir)) { fail("Could not create private save directory: %s",strerror(errno)); goto done; }
    file_data=read_file(rom_path,ZIP_LIMIT,&file_bytes);
    if(!file_data) { fail("Could not read ROM: %s",strerror(errno)); goto done; }
    rom_data=file_data; rom_bytes=file_bytes;
    if(file_bytes>=4&&le32(file_data)==0x04034b50) {
        rom_data=unzip(file_data,file_bytes,&rom_bytes);
        if(!rom_data) { fail("ZIP must contain a valid stored/deflated SNES ROM"); goto done; }
        free(file_data); file_data=NULL;
    }
    if(rom_bytes<32768||rom_bytes>ROM_LIMIT) { fail("Unsupported SNES ROM size"); goto done; }
    s.rom_crc=(uint32_t)crc32(0,rom_data,(uInt)rom_bytes); s.rom_bytes=(uint32_t)rom_bytes;
    if(!fingerprint(core_path,&s.core_crc,&s.core_bytes)) { fail("Could not identify core file"); goto done; }
    snprintf(s.sram_path,sizeof(s.sram_path),"%s/game-%08x-%u.srm",save_dir,s.rom_crc,s.rom_bytes);
    snprintf(s.state_path,sizeof(s.state_path),"%s/game-%08x-%u-core-%08x-%u.state",save_dir,s.rom_crc,s.rom_bytes,s.core_crc,s.core_bytes);
    snprintf(s.report_path,sizeof(s.report_path),"%s/last-session.txt",save_dir);
    progress("core_loading",1);
    s.core=dlopen(core_path,RTLD_NOW|RTLD_LOCAL);
    if(!s.core) { fail("Could not load core: %s",dlerror()); goto done; }
#define LOAD(type,name,args) do { *(void **)(&p_##name)=dlsym(s.core,#name); if(!p_##name) { fail("Core lacks " #name); goto done; } } while(0);
    CORE_FUNCTIONS(LOAD)
#undef LOAD
    if(p_retro_api_version()!=RETRO_API_VERSION) { fail("Unsupported libretro API version"); goto done; }
    memset(&info,0,sizeof(info)); p_retro_get_system_info(&info);
    if(info.need_fullpath) { fail("MVP requires the known memory-loading Plus core"); goto done; }
    p_retro_set_environment(environment); p_retro_set_video_refresh(video);
    p_retro_set_audio_sample(audio_sample); p_retro_set_audio_sample_batch(audio_batch);
    p_retro_set_input_poll(input_poll); p_retro_set_input_state(input_state);
    p_retro_init(); s.initialized=true;
    if(!s.pixel_format) { fail("Core did not negotiate RGB565"); goto done; }
    memset(&game,0,sizeof(game)); game.path=rom_path; game.data=rom_data; game.size=rom_bytes;
    if(!p_retro_load_game(&game)) { fail("Core rejected game"); goto done; }
    s.loaded=true;
    /* Pinned Plus copies load-from-memory input synchronously, as in v11.
     * Reclaim the whole file rather than keeping a duplicate ROM during play. */
    if(rom_data!=file_data) free(rom_data);
    free(file_data); rom_data=file_data=NULL;
    p_retro_get_system_av_info(&native_av);
    if(!valid_av(&native_av)) { fail("Core AV timing/geometry outside SNES MVP contract"); goto done; }
    s.input_rate=(unsigned)native_av.timing.sample_rate;
    if((double)s.input_rate!=native_av.timing.sample_rate) { fail("Fractional native sample rate needs a different converter"); goto done; }
    if(!load_sram()) goto done;
    save_ready=true;
    p_retro_set_controller_port_device(0,RETRO_DEVICE_JOYPAD);
    actual_rate=board_audio_open(s.input_rate);
    if(actual_rate<0) { fail("Audio open failed: %s",board_last_error()); goto done; }
    s.audio_open=true;
    if(actual_rate<8000 || actual_rate>48000) { fail("Unsupported negotiated PCM rate: %d",actual_rate); goto done; }
    s.output_rate=(unsigned)actual_rate;
    s.audio_ready=true; audio_reset();
    if(!prime_audio()) goto done;
    if(board_is_null()) {
        value=getenv("D35_MVP_FRAMES");
        if(value&&*value) {
            while(*value>='0'&&*value<='9'&&limit<10000000u) limit=limit*10u+(unsigned)(*value++-'0');
            if(*value||!limit||limit>10000000u) { fail("Invalid bounded mock frame count"); goto done; }
        }
        value=getenv("D35_MVP_NO_PACING"); no_pacing=value&&!strcmp(value,"1");
    }
    fraction=1000000000.0/native_av.timing.fps; period=(uint64_t)fraction; fraction-=period;
    deadline=board_now_ns(); s.start_ns=deadline;
    progress("running",1);
    while(!s.failed&&!stop_requested&&(!limit||s.runs<limit)) {
        uint64_t began,elapsed,cpu_start,cpu_end,step_start=board_now_ns();
        unsigned bin; uint32_t buttons=board_poll_input();
        if((buttons&BOARD_MENU)&&!(old_buttons&BOARD_MENU)) {
            if(!pause_menu()) break;
            deadline=board_now_ns(); remainder=0; old_buttons=board_poll_input(); continue;
        }
        old_buttons=buttons;
        pump_audio();
        /* Reserve at least2048 output frames before entering the core. Never
         * let a full sink silently discard a callback the core won't replay. */
        { uint64_t wait=board_now_ns();
          if(audio_pipe_admit(2048,!no_pacing && !board_is_null())<0) fail("Audio admission failed: %s",strerror(errno));
          s.audio_space_wait_ns+=board_now_ns()-wait; }
        if(s.failed||stop_requested) break;
        if(!no_pacing && board_is_null()) {
            uint64_t before=board_now_ns(); board_sleep_until(deadline);
            s.pacing_wait_ns+=board_now_ns()-before;
        }
        if(board_video_reserve()<0) { fail("Display queue stalled: %s",board_last_error()); break; }
        s.buttons=board_poll_input(); /* fresh input after admission */
        if(board_now_ns()>deadline+period) {
            uint64_t late=board_now_ns()-deadline; ++s.late_calls;
            if(late>s.max_lateness_ns) s.max_lateness_ns=late;
        }
        cpu_start=thread_cpu_ns(); began=board_now_ns();
        p_retro_run();
        board_video_cancel();
        elapsed=board_now_ns()-began; cpu_end=thread_cpu_ns(); ++s.runs;
        s.wall_ns+=elapsed; if(cpu_end>=cpu_start) s.cpu_ns+=cpu_end-cpu_start;
        if(s.max_run_ns<elapsed) s.max_run_ns=elapsed;
        bin=(unsigned)(elapsed/1000000u); if(bin>=ARRAY_SIZE(s.run_hist)) bin=ARRAY_SIZE(s.run_hist)-1;
        ++s.run_hist[bin]; pump_audio();
        progress(s.failed?"failed":"running",0);
        s.active_ns+=board_now_ns()-step_start;
        deadline+=period; remainder+=fraction;
        if(remainder>=1.0) { ++deadline; remainder-=1.0; }
        /* A long OS/device stall is a reported discontinuity, not minutes of
         * accelerated catch-up. Ordinary render debt remains for adaptation. */
        if(board_now_ns()>deadline+250000000u) deadline=board_now_ns();
    }
done:
    if(s.report_path[0]) progress(s.failed?"failed_before_cleanup":"cleanup",1);
    audio_pipe_stop(!s.failed); pump_audio();
    if(s.audio_open) {
        (void)board_audio_reset(); board_audio_close(); s.audio_ready=false;
    }
    board_video_cancel();
    board_wait_display();
    if(s.loaded&&save_ready&&!s.state_unsafe) {
        bool stored=save_sram();
        if(!stored&&!s.failed) fail("Could not save in-game progress; previous generation retained");
        if(stored&&!s.failed) status(p_retro_get_memory_size(RETRO_MEMORY_SAVE_RAM)?
            "Game closed. In-game save stored.":"Game closed.");
    }
    if(s.loaded) p_retro_unload_game();
    if(s.initialized) p_retro_deinit();
    if(s.core) dlclose(s.core);
    if(s.report_path[0]) { progress("finished",1); report(); }
    if(rom_data!=file_data) free(rom_data);
    free(file_data);
    return s.failed?-1:0;
}
