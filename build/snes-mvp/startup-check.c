/* Exercise the real launcher entry and input event code with stuck GPIO bits. */
#define main launcher_main
#include "main.c"
#undef main
#include <assert.h>
#include "timing.h"
static uint32_t raw_keys;
static uint64_t fake_now;
static unsigned submitted, polled, slept;
static int boot_fixture;
int board_open(int mode) { assert(mode); return 0; }
void board_close(void) {}
void board_set_input_trace(int enabled) { (void)enabled; }
const char *board_last_error(void) { return "fixture"; }
int board_video_submit(const void *p,unsigned w,unsigned h,size_t pitch)
{
    assert(p && w==UI_WIDTH && h==UI_HEIGHT && pitch==UI_WIDTH*2);
    if(boot_fixture==1) { assert(!polled); quitting=1; }
    ++submitted; return 0;
}
void board_wait_display(void) { assert(submitted); }
uint32_t board_poll_input(void)
{
    if(boot_fixture) assert(submitted);
    ++polled;
    if(boot_fixture==2) {
        switch(polled) {
        case 3: return KEY(DOWN);
        case 5: return KEY(UP);
        case 7: case 8: return KEY(A); /* Launch and held-button suppression. */
        default: assert(polled<7); return 0;
        }
    }
    return raw_keys;
}
uint64_t board_now_ns(void) { return boot_fixture==2?timing_now_ns():fake_now; }
void board_sleep_until(uint64_t deadline)
{
    assert(++slept<12);
    if(boot_fixture==2) timing_sleep_until(deadline);
    else fake_now=deadline;
}
void runner_set_menu_callback(runner_menu_callback callback,void *userdata)
{ (void)callback; (void)userdata; }
void runner_set_initial_sram(const char *path) { (void)path; }
void runner_request_stop(void) {}
const char *runner_last_error(void) { return "fixture"; }
const char *runner_last_status(void) { return "fixture"; }
int runner_run(const char *rom,const char *core,const char *saves)
{
    (void)core; (void)saves;
    assert(boot_fixture==2 && strstr(rom,"/clock-a.sfc"));
    quitting=1; return 0;
}
int main(int argc,char **argv)
{
    char *args[]={"startup-check","--mock","--base",NULL,NULL};
    assert(argc==2); args[3]=argv[1];
    boot_fixture=1;
    raw_keys=KEY(A)|KEY(DOWN)|KEY(L2)|KEY(R2)|BOARD_MENU;
    assert(!launcher_main(4,args));
    assert(submitted==1 && polled==1 && slept==0);
    puts("PASS: real launcher first frame completes with permanently held input; no release wait");
    boot_fixture=0; quitting=0;
    prime_input();
    fake_now+=5000000000ull;
    assert(events()==0); /* No initial activate, cancel or navigation repeat. */
    raw_keys|=KEY(UP);
    assert(events()==KEY(UP));
    raw_keys&=~(KEY(A)|KEY(DOWN)|KEY(UP));
    assert(!events());
    raw_keys|=KEY(A);
    assert(events()==KEY(A)); /* Released button can be pressed again. */
    raw_keys&=~KEY(A);
    assert(!events());
    raw_keys|=KEY(DOWN);
    assert(events()==KEY(DOWN));
    fake_now+=400000000ull;
    assert(events()==KEY(DOWN)); /* Repeat remains usable despite stuck L2/R2. */
    puts("PASS: initial held buttons suppressed independently; new presses and navigation repeat work");
    {
        char dir[PATH_CAP],path[PATH_CAP]; FILE *f; uint64_t start;
        char *live_args[]={"startup-check","--mock","--base",argv[1],"--romdir",dir,NULL};
        assert(join(dir,sizeof(dir),argv[1],"clock-library"));
        assert(mkdir(dir,0755)==0 || errno==EEXIST);
        assert(join(path,sizeof(path),dir,"clock-a.sfc")); f=fopen(path,"wb"); assert(f); fputc(0,f); fclose(f);
        assert(join(path,sizeof(path),dir,"clock-b.sfc")); f=fopen(path,"wb"); assert(f); fputc(0,f); fclose(f);
        boot_fixture=2; quitting=0; polled=submitted=slept=0;
        start=timing_now_ns();
        assert(!launcher_main(6,live_args));
        assert(polled==8 && submitted==4 && slept==5);
        assert(timing_now_ns()-start<1500000000ull);
        puts("PASS: real launcher menu keeps polling through kernel-clock waits; Down/Up/A launch selected game");
    }
    return 0;
}
