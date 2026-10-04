/* Real pinned Plus core/ROM/state, mock hardware only. */
#define RUNNER_CHECK_CUSTOM_POLL
#define main runner_contract_main
#include "runner-check.c"
#undef main
static unsigned menu_count, menu_triggered;
uint32_t board_poll_input(void)
{
    if(s.runs>=2&&!menu_triggered) { menu_triggered=1; return BOARD_MENU; }
    return 0;
}
static int integration_menu(void *userdata,const char *text)
{
    (void)userdata;
    if(!menu_count++) return RUNNER_LOAD_STATE;
    assert(!strcmp(text,"Snapshot loaded"));
    puts("PASS: runner menu validated and loaded converted v11 snapshot");
    return RUNNER_RESUME;
}
int main(int argc,char **argv)
{
    int rc; size_t bytes; void *p;
    assert(argc==4);
    assert(!setenv("D35_MVP_FRAMES","120",1));
    assert(!setenv("D35_MVP_NO_PACING","1",1));
    runner_set_menu_callback(integration_menu,NULL);
    rc=runner_run(argv[1],argv[2],argv[3]);
    if(rc) fprintf(stderr,"runner error: %s\n",runner_last_error());
    assert(!rc&&menu_count==2&&s.runs==120&&s.pauses==1&&s.primed==4096);
    p=read_file(s.sram_path,ROM_LIMIT,&bytes); assert(p&&bytes); free(p);
    assert(!strcmp(runner_last_status(),"Game closed. In-game save stored."));
    printf("PASS: real Plus runner120 frames, imported snapshot resume, private SRAM%u bytes, clean exit\n",(unsigned)bytes);
    printf("ROM=%08x core=%08x submitted=%llu held=%llu native_audio=%llu\n",s.rom_crc,s.core_crc,
        (unsigned long long)s.videos,(unsigned long long)s.held,(unsigned long long)s.generated);
    return 0;
}
