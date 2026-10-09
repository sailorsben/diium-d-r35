/* Offline owner-supplied game inspection. Never install on the handheld.
 * Commands and derived states stay in a private output directory; memory edits
 * affect this process only. Reuse the qualified libretro loader and CRC sinks. */
#define main d35_equivalence_main
#include "plus-a7-equivalence.c"
#undef main
static uint16_t buttons;
static unsigned char image_bytes[512*478*2];
static unsigned image_w,image_h;
static uint64_t total_frames;
static unsigned number(const char *s,unsigned base)
{
    unsigned value=0;assert(s && *s);
    if(base==16 && s[0]=='0' && s[1]=='x')s+=2;
    assert(*s);
    while(*s && *s!='\n' && *s!='\r') {
        unsigned d=*s>='0'&&*s<='9'?(unsigned)(*s-'0'):
            *s>='a'&&*s<='f'?(unsigned)(*s-'a'+10):
            *s>='A'&&*s<='F'?(unsigned)(*s-'A'+10):99;
        assert(d<base && value<=(UINT32_MAX-d)/base);value=value*base+d;s++;
    }
    return value;
}
static void replay_video(const void *p,unsigned w,unsigned h,size_t pitch)
{
    assert(p && w<=512 && h<=478);image_w=w;image_h=h;
    for(unsigned y=0;y<h;y++)memcpy(image_bytes+y*w*2,(const char *)p+y*pitch,w*2);
    video_cb(p,w,h,pitch);
}
static int16_t replay_input(unsigned port,unsigned device,unsigned index,unsigned id)
{
    (void)index;if(port || device!=RETRO_DEVICE_JOYPAD)return 0;
    return id==RETRO_DEVICE_ID_JOYPAD_MASK?(int16_t)buttons:id<16?(buttons>>id)&1:0;
}
static void put_le32(unsigned char *p,uint32_t n)
{ for(unsigned i=0;i<4;i++)p[i]=(unsigned char)(n>>(i*8)); }
static void write_image(const char *dir)
{
    char path[1024];assert(image_w && image_h);
    assert(snprintf(path,sizeof(path),"%s/last.ppm",dir)>0);
    FILE *out=fopen(path,"wb");assert(out);fprintf(out,"P6\n%u %u\n255\n",image_w,image_h);
    for(unsigned i=0;i<image_w*image_h;i++) {
        uint16_t p;memcpy(&p,image_bytes+i*2,2);
        unsigned char rgb[3]={(unsigned char)(((p>>11)&31)*255/31),
            (unsigned char)(((p>>5)&63)*255/63),(unsigned char)((p&31)*255/31)};
        assert(fwrite(rgb,1,3,out)==3);
    }
    assert(!fclose(out));
}
int main(int argc,char **argv)
{
    assert(argc==6); /* core, ROM, snapshot or -, SRAM or -, existing output dir */
    struct core c={0};size_t rom_n,core_n,n;
    unsigned char *rom=read_all(argv[2],&rom_n),*core=read_all(argv[1],&core_n);
    open_core(&c,argv[1],rom,rom_n);
    void *(*get_memory_data)(unsigned);size_t (*get_memory_size)(unsigned);
    *(void **)(&get_memory_data)=dlsym(c.handle,"retro_get_memory_data");
    *(void **)(&get_memory_size)=dlsym(c.handle,"retro_get_memory_size");
    assert(get_memory_data && get_memory_size);
    if(strcmp(argv[3],"-")) {
        unsigned char *state=read_all(argv[3],&n);
        assert(n==c.serialize_size()+40 && !memcmp(state,"D35MVP01",8));
        assert(c.unserialize(state+40,n-40));free(state);
    }
    if(strcmp(argv[4],"-")) {
        unsigned char *sram=read_all(argv[4],&n);size_t size=get_memory_size(RETRO_MEMORY_SAVE_RAM);
        assert(n==size && get_memory_data(RETRO_MEMORY_SAVE_RAM));
        memcpy(get_memory_data(RETRO_MEMORY_SAVE_RAM),sram,n);free(sram);
    }
    c.set_video_refresh(replay_video);c.set_input_state(replay_input);
    unsigned char *ram=get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
    size_t ram_n=get_memory_size(RETRO_MEMORY_SYSTEM_RAM);assert(ram && ram_n==0x20000);
    void (*census_read)(unsigned long long *);
    *(void **)(&census_read)=dlsym(c.handle,"d35_census_read");
    char path[1024],line[256];assert(snprintf(path,sizeof(path),"%s/commands.txt",argv[5])>0);
    FILE *commands=fopen(path,"a");assert(commands);
    FILE *census=NULL;
    if(census_read) {
        assert(snprintf(path,sizeof(path),"%s/census.txt",argv[5])>0);
        census=fopen(path,"a");assert(census);
        unsigned long long initial[128];census_read(initial);
    }
    puts("READY: advance decimal-frames hex-libretro-mask; image; save; peek hex-offset decimal-length; poke hex-offset hex-byte; quit");fflush(stdout);
    while(fgets(line,sizeof(line),stdin)) {
        fputs(line,commands);assert(!fflush(commands));
        char *op=strtok(line," \r\n"),*a=strtok(NULL," \r\n"),*b=strtok(NULL," \r\n");
        if(!op)continue;
        if(!strcmp(op,"quit"))break;
        if(!strcmp(op,"advance")) {
            unsigned count=number(a,10);buttons=(uint16_t)number(b,16);assert(count && count<=10000);
            for(unsigned f=0;f<count;f++) {
                frame=(unsigned)total_frames;c.run();total_frames++;
                if(census) {
                    unsigned long long counts[128];census_read(counts);
                    fprintf(census,"CENSUS frame=%llu",(unsigned long long)total_frames);
                    for(unsigned i=0;i<128;i++)fprintf(census," %llu",counts[i]);
                    fputc('\n',census);
                }
            }
            if(census)assert(!fflush(census));
            printf("advanced=%u total=%llu pixels=%08x pcm=%08x\n",count,(unsigned long long)total_frames,c.pixels,c.pcm);
        } else if(!strcmp(op,"image"))write_image(argv[5]);
        else if(!strcmp(op,"peek")) {
            unsigned offset=number(a,16),count=number(b,10);assert(count<=256 && offset+count<=ram_n);
            printf("ram[%05x]",offset);for(unsigned i=0;i<count;i++)printf(" %02x",ram[offset+i]);puts("");
        } else if(!strcmp(op,"poke")) {
            unsigned offset=number(a,16),value=number(b,16);assert(offset<ram_n && value<=255);ram[offset]=(unsigned char)value;
        } else if(!strcmp(op,"save")) {
            size_t size=c.serialize_size();unsigned char header[40]={0},*state=malloc(size);assert(state && c.serialize(state,size));
            memcpy(header,"D35MVP01",8);put_le32(header+8,1);put_le32(header+12,crc32(0,rom,rom_n));
            put_le32(header+16,rom_n);put_le32(header+20,crc32(0,core,core_n));put_le32(header+24,core_n);
            put_le32(header+28,size);put_le32(header+32,crc32(0,state,size));
            assert(snprintf(path,sizeof(path),"%s/scene.state",argv[5])>0);
            FILE *out=fopen(path,"wb");assert(out && fwrite(header,1,40,out)==40 && fwrite(state,1,size,out)==size);
            assert(!fclose(out));free(state);puts("saved private derived state");
        } else { fprintf(stderr,"Unknown command\n");return 2; }
        fflush(stdout);
    }
    assert(!fclose(commands));if(census)assert(!fclose(census));
    c.unload_game();c.deinit();dlclose(c.handle);free(rom);free(core);return 0;
}
