#define _GNU_SOURCE
#include "board.h"
#include "runner.h"
#include "ui.h"
#include "startup.h"
#include <libretro.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <strings.h>
#include <dirent.h>
#include <sys/stat.h>
#include <signal.h>
#include <errno.h>
#include <unistd.h>

#define GAME_LIMIT 256
#define PATH_CAP 1024
#define KEY(x) (1u << RETRO_DEVICE_ID_JOYPAD_##x)
struct game { char path[PATH_CAP], name[256]; };
static volatile sig_atomic_t quitting;
static char current_name[256];
static uint32_t previous_keys;
static uint32_t suppressed_keys;
static uint64_t next_repeat;
static void signal_exit(int sig) { (void)sig; quitting = 1; runner_request_stop(); }
static int join(char *out, size_t cap, const char *dir, const char *leaf)
{ int n=snprintf(out,cap,"%s/%s",dir,leaf); return n>=0 && (size_t)n<cap; }
static int supported(const char *name)
{
    const char *e=strrchr(name,'.');
    return e && (!strcasecmp(e,".zip") || !strcasecmp(e,".sfc") || !strcasecmp(e,".smc"));
}
static int game_order(const void *a,const void *b)
{ return strcasecmp(((const struct game *)a)->name,((const struct game *)b)->name); }
static size_t scan(const char *dir,struct game *games,size_t count)
{
    DIR *d=opendir(dir); struct dirent64 *entry;
    if (!d) return count;
    /* Explicit large inode entries also work when the same ARM binary is
     * tested against an NTFS-mounted host directory under QEMU. */
    while (count<GAME_LIMIT && (entry=readdir64(d))) {
        struct stat st; size_t j; char *dot;
        if (!supported(entry->d_name) || !join(games[count].path,PATH_CAP,dir,entry->d_name)) continue;
        if (entry->d_type!=DT_REG && (stat(games[count].path,&st) || !S_ISREG(st.st_mode))) continue;
        for(j=0;j<count;j++) if(!strcmp(games[j].path,games[count].path)) break;
        if(j<count) continue;
        snprintf(games[count].name,sizeof(games[count].name),"%s",entry->d_name);
        dot=strrchr(games[count].name,'.'); if(dot) *dot=0;
        count++;
    }
    closedir(d); return count;
}
static uint32_t events(void)
{
    uint32_t raw=board_poll_input(), keys, edge;
    /* A held or unwired pin cannot trap a menu or launch a game on entry.
     * Suppress each initially held button independently until it releases. */
    suppressed_keys &= raw;
    keys=raw & ~suppressed_keys;
    edge=keys & ~previous_keys;
    uint32_t nav=keys & (KEY(UP)|KEY(DOWN)|KEY(LEFT)|KEY(RIGHT));
    uint64_t now=board_now_ns();
    if ((keys ^ previous_keys) & (KEY(UP)|KEY(DOWN)|KEY(LEFT)|KEY(RIGHT))) next_repeat=now+350000000ull;
    else if(nav && now>=next_repeat) { edge |= nav; next_repeat=now+100000000ull; }
    previous_keys=keys;
    return edge;
}
static void prime_input(void)
{
    suppressed_keys=board_poll_input();
    previous_keys=0;
    next_repeat=board_now_ns()+350000000ull;
    startup_note("input baseline held_mask=0x%08x",suppressed_keys);
}
static int present(uint16_t *pixels)
{
    if(board_video_submit(pixels,UI_WIDTH,UI_HEIGHT,UI_WIDTH*2u)<0) {
        fprintf(stderr,"display: %s\n",board_last_error()); quitting=1; return -1;
    }
    return 0;
}
static int pause_menu(void *userdata,const char *status)
{
    uint16_t *pixels=malloc(UI_WIDTH*UI_HEIGHT*2u);
    unsigned selected=0; int dirty=1, result=RUNNER_EXIT;
    (void)userdata;
    if(!pixels) return RUNNER_RESUME;
    ui_draw_pause(pixels,UI_WIDTH,current_name,selected,status);
    if(present(pixels)<0) { free(pixels); return RUNNER_EXIT; }
    dirty=0;
    board_set_input_trace(1);
    prime_input();
    while(!quitting) {
        uint32_t e;
        if(dirty) { ui_draw_pause(pixels,UI_WIDTH,current_name,selected,status); if(present(pixels)<0) break; dirty=0; }
        e=events();
        if(e & KEY(UP)) { selected=(selected+UI_PAUSE_COUNT-1)%UI_PAUSE_COUNT; dirty=1; }
        if(e & KEY(DOWN)) { selected=(selected+1)%UI_PAUSE_COUNT; dirty=1; }
        if(e & (KEY(B)|BOARD_MENU)) { result=RUNNER_RESUME; break; }
        if(e & (KEY(A)|KEY(START))) { result=(int)selected; break; }
        board_sleep_until(board_now_ns()+8000000ull);
    }
    board_wait_display(); free(pixels); board_set_input_trace(0); prime_input(); return result;
}
static int write_ppm(const char *path,const uint16_t *pixels)
{
    FILE *f=fopen(path,"wb"); size_t i; int ok;
    if(!f) return -1;
    fprintf(f,"P6\n640 480\n255\n");
    for(i=0;i<UI_WIDTH*UI_HEIGHT;i++) {
        unsigned p=pixels[i]; unsigned char rgb[3]={(unsigned char)(((p>>11)&31)*255/31),
            (unsigned char)(((p>>5)&63)*255/63),(unsigned char)((p&31)*255/31)};
        if(fwrite(rgb,1,3,f)!=3) { fclose(f); return -1; }
    }
    ok=!ferror(f); if(fclose(f)) ok=0; return ok?0:-1;
}
static int preview(const char *dir)
{
    const char *names[]={"Chrono Trigger","Final Fantasy VI","Final Fantasy VI (Rev 1)","Super Mario World","The Legend of Zelda"};
    uint16_t *p=malloc(UI_WIDTH*UI_HEIGHT*2u); char path[PATH_CAP]; int rc=0;
    if(!p) return 1;
    if(mkdir(dir,0755)<0 && errno!=EEXIST) { free(p); return 1; }
    ui_draw_library(p,UI_WIDTH,names,5,1,"SNES Plus  |  MVP 1");
    if(!join(path,sizeof(path),dir,"library.ppm") || write_ppm(path,p)) rc=1;
    ui_draw_pause(p,UI_WIDTH,"Final Fantasy VI",1,"Your in-game saves are kept separately.");
    if(!join(path,sizeof(path),dir,"pause.ppm") || write_ppm(path,p)) rc=1;
    ui_draw_library(p,UI_WIDTH,NULL,0,0,"Copy .sfc, .smc or .zip files into ROMs/SNES.");
    if(!join(path,sizeof(path),dir,"empty.ppm") || write_ppm(path,p)) rc=1;
    free(p); return rc;
}
int main(int argc,char **argv)
{
    const char *dirs[8]={"/media/sdcardb1/002","/media/sdcardb1/ROMs/SNES"}; size_t dir_count=2;
    const char *base="/usr/retro/snes-mvp", *core="/usr/retro/libs/emu_sfc_plus.so", *rom=NULL, *sram=NULL;
    const char *save_override=NULL; char saves[PATH_CAP], remembered[PATH_CAP]="", status[256]="SNES Plus  |  MVP 1";
    int mock=0,list=0,i,rc=0;
    for(i=1;i<argc;i++) {
        if(!strcmp(argv[i],"--mock")) mock=1;
        else if(!strcmp(argv[i],"--list")) list=1;
        else if(!strcmp(argv[i],"--preview") && i+1<argc) return preview(argv[++i]);
        else if(!strcmp(argv[i],"--base") && i+1<argc) base=argv[++i];
        else if(!strcmp(argv[i],"--core") && i+1<argc) core=argv[++i];
        else if(!strcmp(argv[i],"--rom") && i+1<argc) rom=argv[++i];
        else if(!strcmp(argv[i],"--sram") && i+1<argc) sram=argv[++i];
        else if(!strcmp(argv[i],"--saves") && i+1<argc) save_override=argv[++i];
        else if(!strcmp(argv[i],"--romdir") && i+1<argc && dir_count<8) dirs[dir_count++]=argv[++i];
        else { fprintf(stderr,"Usage: %s [--rom file] [--core core.so] [--base dir] [--saves dir] [--romdir dir] [--sram copy.srm] [--mock] [--list] [--preview dir]\n",argv[0]); return 2; }
    }
    if(save_override) { if(strlen(save_override)>=sizeof(saves)) return 2; strcpy(saves,save_override); }
    else if(!join(saves,sizeof(saves),base,"saves")) return 2;
    if(list) {
        struct game *g=calloc(GAME_LIMIT,sizeof(*g)); size_t n=0,j;
        if(!g) return 1;
        for(j=0;j<dir_count;j++) n=scan(dirs[j],g,n);
        qsort(g,n,sizeof(*g),game_order); for(j=0;j<n;j++) printf("%s\t%s\n",g[j].name,g[j].path);
        free(g); return 0;
    }
    signal(SIGINT,signal_exit); signal(SIGTERM,signal_exit);
    startup_begin();
    if(board_open(mock)<0) {
        startup_note("board failed: %s",board_last_error()); startup_end();
        fprintf(stderr,"board: %s\n",board_last_error()); return 1;
    }
    startup_note("board open complete");
    runner_set_menu_callback(pause_menu,NULL); runner_set_initial_sram(sram);
    if(rom) {
        const char *leaf=strrchr(rom,'/'); snprintf(current_name,sizeof(current_name),"%s",leaf?leaf+1:rom);
        rc=runner_run(rom,core,saves);
        if(rc) fprintf(stderr,"runner: %s\n",runner_last_error());
    } else while(!quitting) {
        struct game *g=calloc(GAME_LIMIT,sizeof(*g)); const char **names=calloc(GAME_LIMIT,sizeof(*names));
        uint16_t *pixels=malloc(UI_WIDTH*UI_HEIGHT*2u); size_t n=0,j,selected=0;
        char chosen[PATH_CAP]=""; int dirty=1;
        if(!g || !names || !pixels) { free(g); free(names); free(pixels); rc=1; break; }
        startup_note("library scan enter");
        for(j=0;j<dir_count;j++) n=scan(dirs[j],g,n);
        startup_note("library scan complete games=%u",(unsigned)n);
        qsort(g,n,sizeof(*g),game_order);
        for(j=0;j<n;j++) { names[j]=g[j].name; if(!strcmp(remembered,g[j].path)) selected=j; }
        board_set_input_trace(1);
        /* First paint must never depend on all GPIO inputs being released. */
        ui_draw_library(pixels,UI_WIDTH,names,n,selected,status);
        startup_note("first library submit");
        if(present(pixels)<0) {
            free(pixels); free(names); free(g); rc=1; break;
        }
        startup_note("first library wait for display");
        board_wait_display();
        startup_note("first library display complete; input baseline enter");
        prime_input();
        startup_ready();
        dirty=0;
        while(!quitting) {
            uint32_t e;
            if(dirty) { ui_draw_library(pixels,UI_WIDTH,names,n,selected,status); if(present(pixels)<0) break; dirty=0; }
            e=events();
            if(e & KEY(B)) { startup_note("library exit requested by B keys=0x%05x",e); quitting=1; break; }
            if(n && (e & KEY(UP))) { selected=(selected+n-1)%n; dirty=1; }
            if(n && (e & KEY(DOWN))) { selected=(selected+1)%n; dirty=1; }
            if(n && (e & KEY(LEFT))) { selected=selected>UI_LIBRARY_ROWS?selected-UI_LIBRARY_ROWS:0; dirty=1; }
            if(n && (e & KEY(RIGHT))) { selected=selected+UI_LIBRARY_ROWS<n?selected+UI_LIBRARY_ROWS:n-1; dirty=1; }
            if(n && (e & (KEY(A)|KEY(START)))) {
                startup_note("library game launch requested keys=0x%05x selected=%u",e,(unsigned)selected);
                strcpy(chosen,g[selected].path); strcpy(remembered,chosen); strcpy(current_name,g[selected].name);
                ui_draw_notice(pixels,UI_WIDTH,"Starting game",current_name); present(pixels); break;
            }
            board_sleep_until(board_now_ns()+8000000ull);
        }
        board_wait_display(); free(pixels); free(names); free(g);
        if(chosen[0]) {
            board_set_input_trace(0);
            prime_input(); rc=runner_run(chosen,core,saves);
            snprintf(status,sizeof(status),"%s",rc?runner_last_error():runner_last_status());
            fprintf(stderr,"session: %s\n",rc?runner_last_error():runner_last_status());
        }
    }
    startup_note("main exit requested rc=%d quitting=%d",rc,(int)quitting);
    board_close(); startup_end(); return rc;
}
