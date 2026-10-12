/* Independent replay experiments, never recovery of a failed audio epoch. */
#define _GNU_SOURCE
#include "snes-mvp/board.h"
#include "snes-mvp/runner.h"
#include "snes-mvp/startup.h"
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/stat.h>
#include <unistd.h>
static volatile sig_atomic_t stopped;
static void stop(int sig) { (void)sig;stopped=1;runner_request_stop(); }
int main(int argc,char **argv)
{
    const unsigned order[]={0,1,1,0},starts[]={0,261,384},limits[]={500,80,96};
    char dir[1200],core[1200],state[1200],number[32];unsigned passes=0;int failures=0;
    if(argc!=3)return 2; /* owned base and existing owner ROM */
    signal(SIGINT,stop);signal(SIGTERM,stop);startup_begin();
    if(board_open(getenv("D35_PAIR_MOCK")!=NULL)<0) { startup_end();return 1; }
    startup_ready();
    for(unsigned block=0;block<3 && !stopped;block++)for(unsigned k=0;k<4 && !stopped;k++) {
        if(board_poll_input()&BOARD_MENU) { stopped=1;break; }
        unsigned which=order[k];const char *label=which?"combined":"baseline";
        if(snprintf(dir,sizeof(dir),"%s/pass-%02u-start-%u-%s",argv[1],passes,starts[block],label)>=(int)sizeof(dir) ||
           snprintf(core,sizeof(core),"%s/%s.so",argv[1],label)>=(int)sizeof(core) ||
           snprintf(state,sizeof(state),"%s/%s-%u.state",argv[1],label,starts[block])>=(int)sizeof(state)) { failures++;stopped=1;break; }
        if(mkdir(dir,0700)) { failures++;stopped=1;break; }
        setenv("D35_PAIR_STATE",state,1);
        snprintf(number,sizeof(number),"%u",starts[block]);setenv("D35_PAIR_START",number,1);
        snprintf(number,sizeof(number),"%u",limits[block]);setenv("D35_PAIR_LIMIT",number,1);
        fprintf(stderr,"pair pass=%u start=%u variant=%s limit=%u begin\n",passes,starts[block],label,limits[block]);
        if(runner_run(argv[2],core,dir)) { failures++;fprintf(stderr,"pass failed: %s\n",runner_last_error()); }
        if(getenv("D35_PAIR_ABORT"))stopped=1;
        fprintf(stderr,"pair pass=%u workers joined; evidence flushed\n",passes++);sync();
    }
    fprintf(stderr,"pair end passes=%u failures=%d stop=%d\n",passes,failures,(int)stopped);
    board_close();startup_end();return failures?1:0;
}
