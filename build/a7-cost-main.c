/* Owned hardware diagnostic driver; every pass is an independent experiment.
 * A fault terminates its pass. Starting another snapshot pass is never audio
 * recovery or evidence of continuous playback. No library/progress edits. */
#define _GNU_SOURCE
#include "snes-mvp/board.h"
#include "snes-mvp/runner.h"
#include "snes-mvp/startup.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <signal.h>
#include <errno.h>
#include <unistd.h>
static volatile sig_atomic_t stopped;
static void stop(int sig) { (void)sig;stopped=1;runner_request_stop(); }
int main(int argc,char **argv)
{
    /* base, core, ROM (existing card path), separately identified snapshot */
    static const unsigned modes[]={0,1,2,2,0,1,2,2,0,1,2,2,3};
    char saves[1200],mode[16];unsigned p;int failures=0;
    if(argc!=5)return 2;
    signal(SIGINT,stop);signal(SIGTERM,stop);
    if(setenv("D35_COST_STATE",argv[4],1))return 2;
    startup_begin();
    if(board_open(getenv("D35_COST_TEST_MOCK")!=NULL)<0) { fprintf(stderr,"board: %s\n",board_last_error());startup_end();return 1; }
    startup_ready();
    for(p=0;p<sizeof(modes)/sizeof(modes[0]) && !stopped;p++) {
        if(board_poll_input()&BOARD_MENU)break;
        if(snprintf(saves,sizeof(saves),"%s/pass-%02u-mode-%u",argv[1],p,modes[p])>=(int)sizeof(saves))break;
        if(mkdir(saves,0700)) { fprintf(stderr,"new pass directory rejected errno=%d\n",errno);break; }
        snprintf(mode,sizeof(mode),"%u",modes[p]);setenv("D35_COST_MODE",mode,1);
        fprintf(stderr,"independent diagnostic pass=%u mode=%u begin\n",p,modes[p]);
        if(runner_run(argv[3],argv[2],saves)) {
            ++failures;fprintf(stderr,"pass=%u ended with failure: %s\n",p,runner_last_error());
        }
        fprintf(stderr,"pass=%u ended; worker-stop/flush complete\n",p);
        /* Prevent this pass's delayed writeback competing with the next one. */
        sync();
        /* Peripheral owners already joined before runner returns. */
        if(board_poll_input()&BOARD_MENU)break;
    }
    fprintf(stderr,"suite end passes=%u failures=%d stop=%d\n",p,failures,(int)stopped);
    board_close();startup_end();return failures?1:0;
}
