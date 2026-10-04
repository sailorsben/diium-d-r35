#define _GNU_SOURCE
#include "startup.h"
#include "timing.h"
#include <fcntl.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

/* Bring-up lifecycle and bounded library input only. No per-frame gameplay
 * logging; keep exit/cleanup evidence durable in case the platform resets. */
static FILE *log_file;
static unsigned log_lines;
static pthread_mutex_t log_lock = PTHREAD_MUTEX_INITIALIZER;
void startup_begin(void)
{
    const char *path=getenv("D35_MVP_STARTUP_LOG");
    log_lines=0;
    if(path && *path) log_file=fopen(path,"a");
    startup_note("program entered pid=%ld",(long)getpid());
}
void startup_note(const char *format, ...)
{
    uint64_t now;
    va_list args;
    pthread_mutex_lock(&log_lock);
    if(log_file && log_lines++<192) {
        now=timing_now_ns();
        fprintf(log_file,"%llu.%03llu ",(unsigned long long)(now/1000000000ull),
                (unsigned long long)((now%1000000000ull)/1000000ull));
        va_start(args,format); vfprintf(log_file,format,args); va_end(args);
        fputc('\n',log_file); fflush(log_file); fsync(fileno(log_file));
    }
    pthread_mutex_unlock(&log_lock);
}
void startup_end(void)
{
    pthread_mutex_lock(&log_lock);
    if(log_file) fclose(log_file);
    log_file=NULL;
    pthread_mutex_unlock(&log_lock);
}
void startup_ready(void)
{
    const char *path=getenv("D35_MVP_READY_FILE");
    int fd;
    startup_note("READY: first library frame completed; controls initialized");
    if(path && *path) {
        fd=open(path,O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC,0600);
        if(fd>=0) {
            ssize_t written=write(fd,"ready\n",6);
            close(fd);
            if(written!=6) { unlink(path); startup_note("ready marker write failed"); }
        }
        else startup_note("ready marker creation failed");
    }
    /* Main closes this after board teardown. Ready does not end diagnostics. */
}
