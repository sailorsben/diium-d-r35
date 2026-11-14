/* Custom MP3s share the existing menu mixer. Keep decoding out of gameplay. */
enum { MUSIC_BUILTIN, MUSIC_OFF, MUSIC_MP3, MIX_FRAMES=735,
       MP3_LIMIT=8*1024*1024, MUSIC_NAME_MAX=255 };
#define MUSIC_PREF LAUNCHER "/d35-music.cfg"
#define MUSIC_DIR LAUNCHER "/music"
#define MENU_CHANNEL VAR(0x1b8994,struct sound)

struct mp3_playback {
    uint8_t *data, *first, *input, *end;
    void *decoder;
    unsigned index, samples, channels, rate, phase;
    int16_t decoded[2304], mix[MIX_FRAMES*2];
};

struct menu_music {
    volatile unsigned lock;
    unsigned mode;
    bool configured;
    volatile bool unavailable;
    char name[MUSIC_NAME_MAX+1];
    struct mp3_playback *track;
};
#define MUSIC VAR(0x1c4500,struct menu_music)
_Static_assert(sizeof(struct menu_music)<=0x200, "menu music reservation");

static bool music_filename(const char *name)
{
    unsigned n=0;
    while(name[n]) {
        unsigned char c=name[n++];
        if(n>MUSIC_NAME_MAX || c=='/' || c=='\\' || c==':' || c<32 || c==127) return false;
    }
    return n>4 && name[0]!='.' && name[n-4]=='.' &&
        (name[n-3]|32)=='m' && (name[n-2]|32)=='p' && name[n-1]=='3';
}

static void read_music_setting(void)
{
    if(MUSIC.configured) return;
    MUSIC.configured=true;
    char path[384], value[MUSIC_NAME_MAX+3];
    if(!suffix(path,sizeof(path),WORK(),MUSIC_PREF)) return;
    FILE *f=FOPEN(path,"rb");
    if(!f) return;
    size_t n=FREAD(value,1,sizeof(value)-1,f);
    FCLOSE(f);
    value[n]=0;
    if(n==1 && value[0]=='O') MUSIC.mode=MUSIC_OFF;
    if(n>1 && n<=MUSIC_NAME_MAX+1 && value[0]=='M' && music_filename(value+1)) {
        MUSIC.mode=MUSIC_MP3;
        COPY(MUSIC.name,value+1,n);
    }
}

static void menu_audio_lock(void)
{
    while(__atomic_exchange_n(&MUSIC.lock,1,__ATOMIC_ACQUIRE))
        FN(0x11f08,int,unsigned)(1000);
}

static void menu_audio_unlock(void)
{
    __atomic_store_n(&MUSIC.lock,0,__ATOMIC_RELEASE);
}

static void free_mp3(struct mp3_playback *track)
{
    if(!track) return;
    if(track->decoder) FN(0xa6a30,void,void *)(track->decoder);
    if(track->data) FREE(track->data);
    FREE(track);
}

static bool next_mp3_frame(struct mp3_playback *track)
{
    unsigned scanned=0;
    for(unsigned attempts=0;attempts<12;++attempts) {
        if(track->end-track->input<4) track->input=track->first;
        int remaining=(int)(track->end-track->input);
        unsigned search=(unsigned)remaining;
        if(search>32768u-scanned) search=32768u-scanned;
        if(search<4) return false;
        int sync=FN(0xa6a3c,int,const uint8_t *,int)(track->input,(int)search);
        scanned+=sync<0?search:(unsigned)sync;
        if(sync<0 || sync>remaining-4) {
            if(track->input==track->first) return false;
            track->input=track->first;
            continue;
        }
        track->input+=sync;
        remaining-=sync;
        uint8_t *before=track->input;
        int status=FN(0xa6b74,int,void *,uint8_t **,int *,int16_t *,int)(
            track->decoder,&track->input,&remaining,track->decoded,0);
        if(track->input<=before || track->input>track->end) track->input=before+1;
        if(status) continue;
        int info[7];
        FN(0xa6a90,void,void *,int *)(track->decoder,info);
        if((info[1]!=1 && info[1]!=2) || info[2]<8000 || info[2]>48000 ||
           info[3]!=16 || info[4]<info[1] || info[4]>2304) continue;
        track->index=0;
        track->channels=(unsigned)info[1];
        track->rate=(unsigned)info[2];
        track->samples=(unsigned)info[4]/track->channels;
        return true;
    }
    return false;
}

static struct mp3_playback *open_music(const char *name)
{
    char dir[384], path[672];
    if(!music_filename(name) || !suffix(dir,sizeof(dir),WORK(),MUSIC_DIR "/") ||
       !suffix(path,sizeof(path),dir,name)) return NULL;
    struct mp3_playback *track=ALLOC(sizeof(*track));
    if(!track) return NULL;
    ZERO(track,0,sizeof(*track));
    size_t size;
    track->data=read_bytes(path,MP3_LIMIT,&size);
    if(track->data && size>=4) {
        track->end=track->data+size;
        track->input=track->data;
        /* Skip a checked ID3v2 tag so large album covers don't count as
         * audio sync data. Keep the loop origin at the first audio byte. */
        if(size>=10 && !CMP(track->data,"ID3",3)) {
            const uint8_t *b=track->data;
            unsigned tag=10+((b[6]&127u)<<21)+((b[7]&127u)<<14)+((b[8]&127u)<<7)+(b[9]&127u);
            if(b[5]&16) tag+=10;
            if(tag>=size || (b[6]|b[7]|b[8]|b[9])&128u) { free_mp3(track); return NULL; }
            track->input+=tag;
        }
        track->first=track->input;
        track->decoder=FN(0xa6a2c,void *,void)();
        if(track->decoder && next_mp3_frame(track)) return track;
    }
    free_mp3(track);
    return NULL;
}

static bool render_music(struct mp3_playback *track)
{
    for(unsigned i=0;i<MIX_FRAMES;++i) {
        if(track->index>=track->samples) {
            track->index-=track->samples;
            unsigned skip=track->index;
            if(!next_mp3_frame(track)) return false;
            track->index=skip<track->samples?skip:0;
        }
        const int16_t *sample=track->decoded+track->index*track->channels;
        track->mix[i*2]=sample[0];
        track->mix[i*2+1]=sample[track->channels-1];
        track->phase+=track->rate;
        while(track->phase>=44100) { track->phase-=44100; ++track->index; }
    }
    return true;
}

ENTRY void launcher_menu_mix(void)
{
    if(__atomic_exchange_n(&MUSIC.lock,1,__ATOMIC_ACQUIRE)) return;
    struct mp3_playback *track=MUSIC.track;
    if(track) {
        if(render_music(track)) {
            const struct sound block={track->mix,2,1,1,44100,0,track->mix,
                                      track->mix+MIX_FRAMES*2,0};
            COPY(&MENU_CHANNEL,&block,sizeof(block));
        } else {
            MENU_CHANNEL.data=NULL;
            MUSIC.track=NULL;
            MUSIC.unavailable=true;
            free_mp3(track);
        }
    }
    FN(0x88e60,void,void)();
    if(MUSIC.track) MENU_CHANNEL.data=NULL;
    menu_audio_unlock();
}

static void replace_music(struct mp3_playback *track)
{
    menu_audio_lock();
    if(MENU_CHANNEL.data) FN(0x873f4,void,unsigned)(0);
    struct mp3_playback *old=MUSIC.track;
    MUSIC.track=track;
    menu_audio_unlock();
    free_mp3(old);
}

static bool start_builtin_music(void)
{
    char path[384];
    if(!S.music && suffix(path,sizeof(path),WORK(),LAUNCHER "/d35-menu.pcm")) {
        S.music=read_bytes(path,4u*1024u*1024u,&S.music_bytes);
        if(S.music && (S.music_bytes%4 || S.music_bytes<735*4)) {
            FREE(S.music); S.music=NULL; S.music_bytes=0;
        }
    }
    if(!S.music) return false;
    const struct sound pcm={S.music,2,1,1,44100,1,S.music,
                            (uint8_t *)S.music+S.music_bytes,0};
    FN(0x8750c,void,unsigned,const struct sound *)(0,&pcm);
    return true;
}

ENTRY void launcher_menu_sound_close(unsigned channel)
{
    if(!channel) replace_music(NULL);
    else FN(0x873f4,void,unsigned)(channel);
}

static bool menu_music_override(void)
{
    read_music_setting();
    if(MUSIC.mode==MUSIC_BUILTIN) return false;
    struct mp3_playback *track=MUSIC.mode==MUSIC_MP3?open_music(MUSIC.name):NULL;
    MUSIC.unavailable=MUSIC.mode==MUSIC_MP3 && !track;
    replace_music(track);
    return true;
}

static bool choose_music(unsigned mode,const char *name)
{
    struct mp3_playback *track=NULL;
    char path[384], value[MUSIC_NAME_MAX+2];
    size_t n=1;
    value[0]=mode==MUSIC_OFF?'O':mode==MUSIC_MP3?'M':'D';
    if(mode==MUSIC_MP3) {
        track=open_music(name);
        if(!track) return false;
        for(;name[n-1];++n) value[n]=name[n-1];
    }
    if(!suffix(path,sizeof(path),WORK(),MUSIC_PREF) || !save_config_bytes(path,value,n)) {
        free_mp3(track);
        return false;
    }
    replace_music(track);
    MUSIC.mode=mode;
    MUSIC.unavailable=false;
    MUSIC.name[0]=0;
    if(mode==MUSIC_MP3) { COPY(MUSIC.name,value+1,n-1); MUSIC.name[n-1]=0; }
    if(mode==MUSIC_BUILTIN) {
        menu_audio_lock();
        MUSIC.unavailable=!start_builtin_music();
        menu_audio_unlock();
    }
    return true;
}
