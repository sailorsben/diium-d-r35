/* Real suite supervisor with an independently stalled/progressing owned child. */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#include "fivegame-kernel-private-v2/runner/board.h"
#include "fivegame-replay-progress.h"
struct d35_replay_progress *d35_replay_shared;
int board_open(int mock){(void)mock;return 0;}
void board_close(void){}
uint32_t board_poll_input(void){return 0;}
void startup_begin(void){}
void startup_ready(void){}
void startup_end(void){}
void runner_request_stop(void){}
const char *runner_last_error(void){return "";}
int runner_run(const char *rom,const char *core,const char *dir){
    (void)rom;(void)core;(void)dir;assert(d35_replay_shared);
    const char *mode=getenv("D35_SUPERVISOR_FIXTURE");assert(mode);
    d35_replay_shared->epoch=3;d35_replay_shared->calls=123;d35_replay_shared->active=1;
    if(!strcmp(mode,"stall"))for(;;){struct timespec t={0,100000000};syscall(SYS_nanosleep,&t,NULL);}
    if(!strcmp(mode,"progress"))for(unsigned i=0;i<8;i++){
        d35_replay_shared->calls=i+1;struct timespec t={0,100000000};syscall(SYS_nanosleep,&t,NULL);
    }
    if(!strcmp(mode,"abort")){d35_replay_shared->calls=64;setenv("D35_PAIR_ABORT","1",1);}
    d35_replay_shared->active=0;return 0;
}
