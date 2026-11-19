/* Player one's Esc contact shares the stock menu chord. Keep the original
 * menu word intact and retain which contacts actually supplied its bits. */
enum { INPUT_PAIR=9, INPUT_ESC=1u<<16, INPUT_USB_SHIFT=17, INPUT_VALID=1u<<31,
       INPUT_EVENTS=256 };
struct input_event {
    unsigned ms, stage, contacts, native, before, after, pad;
};
struct contact_edge { unsigned sequence, ms, contacts; };
struct input_monitor {
    unsigned pending_pair, sample;
    bool tracing, saved, record_contacts;
    unsigned count, edge_start, edge_count;
    struct input_event events[INPUT_EVENTS];
    struct contact_edge edges[INPUT_EVENTS];
};
#define INPUT VAR(0x1c5000,struct input_monitor)
_Static_assert(sizeof(struct input_monitor)<=0x3000,"input monitor reservation");
enum input_stage { GAME_INPUT, PAUSE_INPUT, SLOT_INPUT, OPEN_SLOTS, SAVE_CALL, SAVE_OK, SAVE_ERROR, CLOSE_SLOTS };
static unsigned input_ms(void);

/* r4 is ReadJoystick's built-in button word at each of the two call sites.
 * The input thread is the only producer. Sample the existing reads, without
 * polling a GPIO twice or configuring a pin. USB port zero joins player one. */
__attribute__((used,noinline)) static int input_escape(unsigned pin,unsigned built_in)
{
    int level=FN(0x157c8,int,unsigned)(pin);
    INPUT.pending_pair=(built_in&INPUT_PAIR) | (level==0?INPUT_ESC:0);
    return level;
}
__attribute__((naked)) ENTRY void input_escape_read(void)
{ __asm__ volatile("mov r1,r4\n\tb input_escape"); }

__attribute__((used,noinline)) static unsigned input_usb(unsigned port,unsigned built_in)
{
    unsigned usb=FN(0x1537c,unsigned,unsigned)(port);
    unsigned contacts=(built_in&~INPUT_PAIR)|INPUT.pending_pair;
    unsigned sample=contacts|((usb&INPUT_PAIR)<<INPUT_USB_SHIFT)|INPUT_VALID;
    unsigned previous=__atomic_load_n(&INPUT.sample,__ATOMIC_RELAXED);
    __atomic_store_n(&INPUT.sample,sample,__ATOMIC_RELEASE);
    if(previous!=sample && __atomic_load_n(&INPUT.record_contacts,__ATOMIC_ACQUIRE)) {
        unsigned n=__atomic_load_n(&INPUT.edge_count,__ATOMIC_RELAXED);
        struct contact_edge *edge=&INPUT.edges[n%INPUT_EVENTS];
        /* Publish the complete sample before making it visible to the reader. */
        __atomic_store_n(&edge->sequence,0,__ATOMIC_SEQ_CST);
        __atomic_store_n(&edge->ms,input_ms(),__ATOMIC_RELAXED);
        __atomic_store_n(&edge->contacts,sample,__ATOMIC_RELAXED);
        __atomic_store_n(&edge->sequence,n+1,__ATOMIC_RELEASE);
        __atomic_store_n(&INPUT.edge_count,n+1,__ATOMIC_RELEASE);
    }
    return usb;
}
__attribute__((naked)) ENTRY void input_usb_read(void)
{ __asm__ volatile("mov r1,r4\n\tb input_usb"); }

static unsigned input_ms(void)
{
    struct { int seconds, nanos; } ts;
    register int call __asm__("r7")=263; /* ARM EABI clock_gettime */
    register int result __asm__("r0")=1; /* CLOCK_MONOTONIC */
    register void *address __asm__("r1")=&ts;
    __asm__ volatile("svc 0":"+r"(result):"r"(call),"r"(address):"memory","cc");
    return result?0:(unsigned)ts.seconds*1000u+(unsigned)ts.nanos/1000000u;
}

static void input_note(enum input_stage stage,unsigned sample,unsigned before,unsigned after)
{
    if(!INPUT.tracing) return;
    unsigned native=VAR(0x1b9b50,const volatile unsigned);
    unsigned n=INPUT.count;
    struct input_event *prev=&INPUT.events[(n-1)%INPUT_EVENTS];
    if(n && prev->stage==(unsigned)stage && prev->contacts==sample && prev->native==native &&
       prev->before==before && prev->after==after) return;
    unsigned pad=0;
    if(stage==GAME_INPUT) {
        for(unsigned id=0;id<16;++id)
            if(FN(0xa2f0c,int16_t,unsigned,unsigned,unsigned,unsigned)(0,1,0,id))
                pad|=1u<<id;
    }
    INPUT.events[n%INPUT_EVENTS]=(struct input_event){input_ms(),stage,sample,native,before,after,pad};
    INPUT.count=n+1;
}

static void input_menu_note(enum input_stage stage)
{
    if(INPUT.tracing)
        input_note(stage,__atomic_load_n(&INPUT.sample,__ATOMIC_ACQUIRE),0,0);
}

ENTRY unsigned input_slot_key(void)
{
    unsigned key=FN(0x86368,unsigned,void)();
    input_menu_note(SLOT_INPUT);
    return key;
}

ENTRY int input_save_slot(const char *path)
{
    input_menu_note(SAVE_CALL);
    int result=stock_save_state(path);
    if(result>0 && INPUT.tracing) INPUT.saved=true;
    input_menu_note(result>0?SAVE_OK:SAVE_ERROR);
    return result;
}

ENTRY void input_game_frame(void)
{
    FN(0xa3654,void,void)(); /* stock turbo and per-player input snapshot */
    unsigned *game=(unsigned *)0x1bd670;
    unsigned before=*game;
    unsigned sample=__atomic_load_n(&INPUT.sample,__ATOMIC_ACQUIRE);
    if(sample&INPUT_VALID) {
        unsigned genuine=(sample | (sample>>INPUT_USB_SHIFT))&INPUT_PAIR;
        *game=before&(~INPUT_PAIR|genuine);
    }
    if(INPUT.tracing) input_note(GAME_INPUT,sample,before,*game);
}

#define INPUT_LOG "/usr/retro/d35-launcher1/ff2-controls.log"
static void input_begin(void)
{
    INPUT.count=0;
    INPUT.saved=false;
    INPUT.tracing=FN(0x11e0c,int,const char *,int)(INPUT_LOG,0)!=0;
    INPUT.edge_start=__atomic_load_n(&INPUT.edge_count,__ATOMIC_ACQUIRE);
    __atomic_store_n(&INPUT.record_contacts,INPUT.tracing,__ATOMIC_RELEASE);
}

static void input_finish(const char *boot)
{
    if(!INPUT.tracing) return;
    INPUT.tracing=false;
    __atomic_store_n(&INPUT.record_contacts,false,__ATOMIC_RELEASE);
    if(!INPUT.saved) return;
    static const char *const phases[]={"game","pause","slot","open-slots","serialize","saved","save-error","close-slots"};
    char *text=ALLOC(256+128*INPUT_EVENTS);
    if(!text) return;
    unsigned first=INPUT.count>INPUT_EVENTS?INPUT.count-INPUT_EVENTS:0;
    int (*print)(char *,const char *,...)=FN(0x11f38,int,char *,const char *,...);
    char *end=text+print(text,"controls=1 boot=%s dropped=%u\nms stage gpio usb_pair native before after retro\n",
                         boot,first);
    for(unsigned i=first;i<INPUT.count;++i) {
        const struct input_event *e=&INPUT.events[i%INPUT_EVENTS];
        end+=print(end,"%u %s %05x %x %08x %08x %08x %04x\n",e->ms,phases[e->stage],
                   e->contacts&0x1ffff,(e->contacts>>INPUT_USB_SHIFT)&INPUT_PAIR,
                   e->native,e->before,e->after,e->pad);
    }
    unsigned limit=__atomic_load_n(&INPUT.edge_count,__ATOMIC_ACQUIRE);
    unsigned available=limit-INPUT.edge_start;
    unsigned lost=available>INPUT_EVENTS?available-INPUT_EVENTS:0;
    end+=print(end,"contact_edges=%u dropped=%u\nms gpio usb_pair\n",available,lost);
    for(unsigned i=INPUT.edge_start+lost;i!=limit;++i) {
        struct contact_edge *e=&INPUT.edges[i%INPUT_EVENTS];
        if(__atomic_load_n(&e->sequence,__ATOMIC_ACQUIRE)!=i+1) continue;
        unsigned ms=__atomic_load_n(&e->ms,__ATOMIC_RELAXED);
        unsigned sample=__atomic_load_n(&e->contacts,__ATOMIC_RELAXED);
        if(__atomic_load_n(&e->sequence,__ATOMIC_SEQ_CST)==i+1)
            end+=print(end,"%u %05x %x\n",ms,sample&0x1ffff,(sample>>INPUT_USB_SHIFT)&INPUT_PAIR);
    }
    save_config_bytes(INPUT_LOG,text,(size_t)(end-text));
    FREE(text);
}
