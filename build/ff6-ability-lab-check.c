/* Original-ROM ability casts through normal inputs; offline correctness only. */
#define main d35_existing_equivalence_main
#include "plus-a7-equivalence.c"
#undef main
static uint16_t lab_buttons[10000];
static unsigned lab_number(const char *s,unsigned base)
{
    unsigned value=0;assert(s && *s);
    while(*s){
        unsigned d=*s>='0'&&*s<='9'?(unsigned)(*s-'0'):
                   *s>='a'&&*s<='f'?(unsigned)(*s-'a'+10):99;
        assert(d<base && value<=(UINT32_MAX-d)/base);value=value*base+d;++s;
    }
    return value;
}
static int16_t lab_input(unsigned port,unsigned device,unsigned index,unsigned id)
{
    (void)index;
    if(port || device!=RETRO_DEVICE_JOYPAD)return 0;
    uint16_t mask=lab_buttons[frame];
    return id==RETRO_DEVICE_ID_JOYPAD_MASK?(int16_t)mask:id<16?(mask>>id)&1:0;
}
int main(int argc,char **argv)
{
    assert(argc==8); /* reference, candidate, ROM, state, buttons, animation ID, calls */
    unsigned effect=lab_number(argv[6],10),calls=lab_number(argv[7],10);
    assert(effect<406 && calls>=600 && calls<=10000);
    FILE *inputs=fopen(argv[5],"r");assert(inputs);
    unsigned duration,mask,used=0;char line[128];
    while(fgets(line,sizeof(line),inputs)){
        char *count=strtok(line," \r\n"),*bits=strtok(NULL," \r\n");
        duration=lab_number(count,10);mask=lab_number(bits,16);
        assert(duration && mask<=65535 && used+duration<=calls);
        for(unsigned i=0;i<duration;i++)lab_buttons[used++]=(uint16_t)mask;
    }
    assert(feof(inputs));fclose(inputs);
    size_t rom_n,state_n;unsigned char *rom=read_all(argv[3],&rom_n),*state=read_all(argv[4],&state_n);
    assert(rom_n==3145728 && state_n>40 && !memcmp(state,"D35MVP01",8));
    unsigned init=rom[0x107fb2+effect*14+10]&127;
    unsigned init_pc=0xc20000u+rom[0x2e8d8+init*2]+(rom[0x2e8d9+init*2]<<8);
    struct core reference={0},candidate={0};
    open_core(&reference,argv[1],rom,rom_n);open_core(&candidate,argv[2],rom,rom_n);
    reference.set_input_state(lab_input);candidate.set_input_state(lab_input);
    size_t size=reference.serialize_size();assert(size==candidate.serialize_size() && state_n==size+40);
    active=&reference;assert(reference.unserialize(state+40,size));
    active=&candidate;assert(candidate.unserialize(state+40,size));
    void (*set_screen)(unsigned),(*set_table)(unsigned),(*read_screen)(unsigned long long *);
    *(void **)(&set_screen)=dlsym(candidate.handle,"d35_screen_set");
    *(void **)(&set_table)=dlsym(candidate.handle,"d35_screen_table_set");
    *(void **)(&read_screen)=dlsym(candidate.handle,"d35_screen_read");
    assert(set_screen && set_table && read_screen);set_screen(init_pc);set_table(effect);
    unsigned char *a=malloc(size),*b=malloc(size);assert(a && b);
    unsigned long long init_hits=0,table_hits=0,deinit_hits=0;
    printf("CASE effect=%u init_pc=%06x rom_overlay=0 input_calls=%u calls=%u\n",effect,init_pc,used,calls);
    for(frame=0;frame<calls;frame++){
        reference.pixels=reference.pcm=reference.videos=0;reference.samples=reference.batches=0;
        candidate.pixels=candidate.pcm=candidate.videos=0;candidate.samples=candidate.batches=0;
        active=&reference;reference.run();active=&candidate;candidate.run();
        if(reference.pixels!=candidate.pixels || reference.pcm!=candidate.pcm ||
           reference.samples!=candidate.samples || reference.videos!=1 || candidate.videos!=1 ||
           reference.w!=candidate.w || reference.h!=candidate.h){
            printf("FAIL output frame=%u pixels=%08x/%08x pcm=%08x/%08x\n",frame,
                   reference.pixels,candidate.pixels,reference.pcm,candidate.pcm);return 2;
        }
        if(!(frame%30)){
            active=&reference;assert(reference.serialize(a,size));
            active=&candidate;assert(candidate.serialize(b,size));normalize_pointers(a);normalize_pointers(b);
            if(memcmp(a,b,size)){printf("FAIL emulated state frame=%u\n",frame);return 3;}
        }
        unsigned long long sc[8];read_screen(sc);init_hits+=sc[0];table_hits+=sc[1];deinit_hits+=sc[3];
    }
    printf("IDENTITY effect=%u init_hits=%llu table_hits=%llu deinit_hits=%llu\n",
           effect,init_hits,table_hits,deinit_hits);
    if(!init_hits || !table_hits || !deinit_hits){puts("FAIL cast identity or completion");return 4;}
    active=&reference;reference.unload_game();reference.deinit();
    active=&candidate;candidate.unload_game();candidate.deinit();
    dlclose(reference.handle);dlclose(candidate.handle);free(a);free(b);free(state);free(rom);
    printf("PASS %u calls: exact graphics/PCM/state, original ROM, requested animation started/completed\n",calls);
    return 0;
}
