/* Offline ARM fixture for the installed launcher. Every hardware seam is
 * intercepted. The real update loop operates on RAM, including a write fault. */
#define D35_STOCK_MENU_ENTRY stock_menu_test
#include "check-stock-shell-menu.c"
#undef D35_STOCK_MENU_ENTRY

enum { IMAGE_BYTES=8*1024*1024, SECTOR=65536 };
static uint8_t flash[IMAGE_BYTES], desired[IMAGE_BYTES];
static uint16_t *shown;
static unsigned frames, waits, reads, erases, writes, starts;
static unsigned last_bar, syncs, sleeps, releases;
static bool drawing, writer_fails, saw_error, saw_complete;

static void *allocate_frame(size_t bytes)
{
    assert(bytes==614400);
    return calloc(1,bytes);
}

static void release_frame(void *frame)
{
    assert(!drawing);
    ++releases;
    free(frame);
}

static void wait_frame(void) { ++waits; drawing=false; }
static void *find_vesper(void *handle,const char *name)
{
    if(handle==&driver && !strcmp(name,"WaitDisp")) return wait_frame;
    assert(!handle && !strcmp(name,"rename"));
    return rename;
}

static void submit(const void *pixels,unsigned width,unsigned height,size_t pitch)
{
    assert(!drawing && pixels && width==640 && height==480 && pitch==1280);
    shown=(void *)pixels;
    assert(shown[40*640+22]!=0xffff);
    unsigned bar=0;
    while(bar<462 && shown[375*640+89+bar]==0x673d) ++bar;
    if(shown[338*640+166]==0xfd49) saw_error=true;
    if(!saw_error) assert(bar>=last_bar);
    if(bar==462) saw_complete=true;
    last_bar=bar;
    ++frames;
    drawing=true;
}

static int delay(unsigned us)
{
    assert(us==185000 || us==850000 || us==1200000);
    ++sleeps;
    return 0;
}
static void save_marker(void) { ++syncs; }

static int fake_read(unsigned offset,void *dest,unsigned size)
{
    assert(offset+size<=sizeof(flash));
    memcpy(dest,flash+offset,size);
    ++reads;
    return 0;
}

static int fake_erase(unsigned offset)
{
    assert(!(offset%SECTOR) && offset+SECTOR<=sizeof(flash));
    memset(flash+offset,255,SECTOR);
    ++erases;
    return 0;
}

static int fake_write(unsigned offset,const void *data,unsigned size)
{
    assert(size==256 && !(offset%size) && offset+size<=sizeof(flash));
    ++writes;
    if(writer_fails) return -1;
    memcpy(flash+offset,data,size);
    return 0;
}

static void update(const char *package)
{
    (void)package;
    ++starts;
    /* The vendor provides dimensions and a chunk-backed buffer to its
     * first display call. These globals are read by the real sector loop. */
    uint16_t *vendor=allocate_frame(614400);
    **(unsigned **)0x19942c=640;
    **(unsigned **)0x19925c=480;
    **(void ***)0x1991f0=vendor;
    ((void (*)(void *,unsigned,unsigned,size_t))target(0x135c0))(vendor,640,480,1280);
    memset(desired,0x21,sizeof(desired));
    memset(flash,0x21,sizeof(flash));
    memset(flash+SECTOR,0x75,SECTOR);
    int status=((int (*)(void *,unsigned))target(0x13950))(desired,sizeof(desired));
    assert(status==!writer_fails && reads>=256 && erases==1+(unsigned)writer_fails*2);
    if(writer_fails) assert(writes==3 && !saw_complete && saw_error);
    else assert(writes==256 && saw_complete && !memcmp(desired,flash,sizeof(flash)));
    free(vendor);
}

static void audio_expectation(void)
{
    char cue_path[4096];
    assert(snprintf(cue_path,sizeof(cue_path),"%s/d35-launcher1/d35-transition.pcm",work)<(int)sizeof(cue_path));
    size_t bytes;
    unsigned char *pcm=read_data(cue_path,&bytes);
    struct sound *effect=(void *)0x1b9d44;
    struct sound *channel=(void *)0x1b89b8;
    uint8_t dummy[4]={0};
    *effect=(struct sound){dummy,2,1,1,44100,0,dummy,dummy+sizeof(dummy),0};
    ((void (*)(unsigned,const struct sound *))target(0x98fc4))(1,effect);
    assert(channel->type==2 && channel->rate==44100 && !channel->loop);
    assert((size_t)((uint8_t *)channel->end-(uint8_t *)channel->begin)==bytes);
    assert(!memcmp(channel->begin,pcm,bytes));
    expected=(const int16_t *)pcm;
    total=bytes/2;
    output=0;
    verify=true;
    void (*mix)(void)=(void *)0x88e60;
    for(size_t i=0;i<total/1470;++i) mix();
    verify=false;
    mix();
    mix();
    assert(!channel->data);
    free(pcm);
}

int main(int argc,char **argv)
{
    assert(argc==3);
    work=argv[2];
    map_vendor(argv[1]);
    patch(0x11ce0,(uintptr_t)fopen); patch(0x11f20,(uintptr_t)fclose);
    patch(0x11b84,(uintptr_t)fseek); patch(0x11e84,(uintptr_t)ftell);
    patch(0x11ed8,(uintptr_t)malloc); patch(0x11ddc,(uintptr_t)fread);
    patch(0x11b6c,(uintptr_t)free); patch(0x11eb4,(uintptr_t)fwrite);
    patch(0x11e0c,(uintptr_t)access); patch(0x11b30,(uintptr_t)save_marker);
    patch(0x11f08,(uintptr_t)delay); patch(0x11be4,(uintptr_t)quiet);
    patch(0x11b48,(uintptr_t)fixed_time);
    patch(0x11c20,(uintptr_t)puts); patch(0x11c8c,(uintptr_t)memset);
    patch(0x11c80,(uintptr_t)putchar);
    patch(0x80bec,(uintptr_t)path); patch(0x12010,(uintptr_t)find_vesper);
    patch(0xa6658,(uintptr_t)submit); patch(0xa695c,(uintptr_t)audio_sink);
    patch(0x164abc,(uintptr_t)allocate_frame); patch(0x164d58,(uintptr_t)release_frame);
    patch(0x133fc,(uintptr_t)update); patch(0x1301c,(uintptr_t)quiet);
    patch(0x12d54,(uintptr_t)fake_read); patch(0x12d90,(uintptr_t)fake_erase);
    patch(0x12db4,(uintptr_t)fake_write);
    *(void **)0x1b81a8=&driver;

    char once[4096], used[4096], code[4096];
    assert(snprintf(once,sizeof(once),"%s/d35-launcher1/vesper-preview.once",work)<(int)sizeof(once));
    assert(snprintf(used,sizeof(used),"%s/d35-launcher1/vesper-preview.used",work)<(int)sizeof(used));
    assert(snprintf(code,sizeof(code),"%s/mock-code.bkp",work)<(int)sizeof(code));
    FILE *marker=fopen(once,"wb");
    assert(marker && !fclose(marker));
    assert(access(code,F_OK));
    void (*entry)(const char *)=(void *)target(0x1231c);
    entry(code);
    assert(!starts && frames==14 && saw_complete && !saw_error && sleeps==14 &&
           releases==1 && syncs==2 && access(once,F_OK) && !access(used,F_OK));
    puts("PASS one-shot renderer from launcher entry, 14 frames, zero SPI calls");

    marker=fopen(code,"wb");
    assert(marker && !fclose(marker));
    last_bar=frames=0; saw_complete=false;
    entry(code);
    assert(starts==1 && frames==101 && saw_complete && releases==2);
    last_bar=frames=reads=erases=writes=0; saw_complete=false; writer_fails=true;
    entry(code);
    assert(starts==2 && !saw_complete && saw_error && releases==3);
    assert(!unlink(code));
    puts("PASS real sector loop against RAM, monotonic progress, and injected SPI write failure");

    audio_expectation();
    puts("PASS Leaf Brush through stock channel and mixer with one-shot end");
    return 0;
}
