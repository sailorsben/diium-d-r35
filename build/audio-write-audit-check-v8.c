#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <dlfcn.h>
#include <assert.h>
static void *display_driver;
static int fake_dsp=9;
static unsigned actual_calls;
static ssize_t next_result;
static int next_error;
static const int16_t *expected;
static ssize_t fake_write(const void *p,size_t bytes)
{
   assert(p==expected && bytes==16); ++actual_calls;
   errno=next_error; return next_result;
}
static void *fake_dlsym(void *handle,const char *name)
{
   assert(handle==(void *)0x35);
   if (!strcmp(name,"DSP")) return &fake_dsp;
   assert(!strcmp(name,"sound_driver_playframe")); return (void *)fake_write;
}
#define dlsym fake_dlsym
#include "device_audio_capture_v8.h"
#include "audio_write_audit_v8.h"
#undef dlsym
int main(void)
{
   int16_t pcm[8]={1,2,3,4,5,6,7,8}, original[8]; expected=pcm;
   memcpy(original,pcm,sizeof(pcm));
   capture_reset(); audit_reset();
   assert(!audit_deliver(pcm,4,1) && audited_fallback==1 && !actual_calls);
   display_driver=(void *)0x35;
   next_result=16; next_error=0; errno=EAGAIN;
   assert(audit_deliver(pcm,4,2) && errno==EAGAIN);
   next_result=8; assert(audit_deliver(pcm,4,3));
   next_result=-1; next_error=EINTR; assert(audit_deliver(pcm,4,4));
   next_result=0; assert(audit_deliver(pcm,4,5));
   next_result=3; assert(audit_deliver(pcm,4,6));
   assert(actual_calls==5 && audited_calls==5 && audited_requested==80 && audited_accepted==27);
   assert(audited_short==2 && audited_errors==1 && audited_zero==1 && audited_unaligned==1);
   assert(audited_first_bad_run==3 && audited_last_bad_run==6 && !memcmp(pcm,original,sizeof(pcm)));
   fake_dsp=-1;
   assert(!audit_deliver(pcm,4,7) && actual_calls==5 && audited_fallback==2);
   setenv("D35_CAPTURE_DIRECTORY",".",1); assert(audit_save());
   capture_feed(pcm,4,1,0); assert(capture_write());
   audit_reset(); assert(!audited_calls && !audited_driver_write);
   puts("PASS driver write audit: exact pointer/bytes, one submission, short/error/zero accounting and fallback");
   return 0;
}
