#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <assert.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
static int chunk_open(const char *, int, ...);
static int chunk_ioctl(int, unsigned long, ...);
static int chunk_close(int);
static void *chunk_dlopen(const char *, int);
static void *chunk_dlsym(void *, const char *);
static int chunk_dlclose(void *);
#define open chunk_open
#define ioctl chunk_ioctl
#define close chunk_close
#define dlopen chunk_dlopen
#define dlsym chunk_dlsym
#define dlclose chunk_dlclose
#include "emu_sfc_plus_v8_capture.c"
#undef open
#undef ioctl
#undef close
#undef dlopen
#undef dlsym
#undef dlclose
static unsigned allocs, frees, waits, closes, displays;
static uint8_t *allocated;
static const uint16_t *last;
static uint16_t last_copy[15];
static uint16_t source[3][8];
static unsigned picture;
static int chunk_open(const char *path, int flags, ...)
{ assert(!strcmp(path, "/dev/chunkmem") && flags == O_RDWR); return 7; }
static void mock_wait(void) { assert(allocated); ++waits; }
static int chunk_ioctl(int fd, unsigned long cmd, ...)
{
   va_list ap; struct chunk_block *b;
   assert(fd == 7);
   va_start(ap, cmd); b = va_arg(ap, struct chunk_block *); va_end(ap);
   assert(sizeof(*b) == 12 && (uint8_t *)&b->mapped - (uint8_t *)b == 4);
   if (cmd == 0xc00c4301u) {
      assert(b->bytes == 1048576 && !allocated);
      allocated = malloc(b->bytes); assert(allocated);
      b->physical = 0x03000000; b->mapped = (uint32_t)(uintptr_t)allocated;
      ++allocs; return 0;
   }
   assert(cmd == 0x400c4303u && waits && b->mapped == (uint32_t)(uintptr_t)allocated);
   free(allocated); allocated = NULL; ++frees; return 0;
}
static int chunk_close(int fd) { assert(fd == 7 && frees); ++closes; return 0; }
static void *chunk_dlopen(const char *path, int flags)
{ (void)flags; assert(!strcmp(path, "/usr/retro/driver.so")); return (void *)0x35; }
static void *chunk_dlsym(void *handle, const char *name)
{ assert(handle == (void *)0x35 && !strcmp(name, "WaitDisp")); return (void *)mock_wait; }
static int chunk_dlclose(void *handle) { assert(handle == (void *)0x35 && frees); return 0; }
static void receive(const void *data, unsigned w, unsigned h, size_t pitch)
{
   const uint16_t *p = data; unsigned x,y;
   assert(w == 5 && h == 3 && pitch == 10);
   if (!data) return;
   assert((uint8_t *)p >= allocated && (uint8_t *)p + 30 <= allocated + 1048576);
   if (last) {
      assert(last != p && !memcmp(last, last_copy, 30));
   }
   for (y = 0; y < 3; ++y) for (x = 0; x < 5; ++x)
      assert(p[y*5+x] == (picture==999 ? 0 : picture*100+y*10+x));
   memcpy(last_copy, p, 30); last = p; ++displays;
}
int main(void)
{
   unsigned x,y;
   frontend_video = receive;
   for (picture = 1; picture <= 3; ++picture) {
      for (y = 0; y < 3; ++y) for (x = 0; x < 8; ++x)
         source[y][x] = picture*100+y*10+x;
      video(source, 5, 3, 16);
   }
   unsigned held_slot=video_slot;
   runs=720; video(source,5,3,16);
   assert(displays==3 && video_slot==held_slot && waits==1);
   assert(!memcmp(last,last_copy,30));
   runs=1440; picture=999; video(source,5,3,16); assert(displays==4);
   runs=2160; picture=5;
   for(y=0;y<3;++y) for(x=0;x<8;++x) source[y][x]=picture*100+y*10+x;
   video(source,5,3,16); assert(displays==5);
   runs=2880; video(source,5,3,16); assert(displays==5 && waits==2);
   runs=3600; picture=999; video(source,5,3,16); assert(displays==6);
   runs=4320; picture=7;
   for(y=0;y<3;++y) for(x=0;x<8;++x) source[y][x]=picture*100+y*10+x;
   video(source,5,3,16); assert(displays==7);
   runs=5040; picture=8;
   for(y=0;y<3;++y) for(x=0;x<8;++x) source[y][x]=picture*100+y*10+x;
   video(source,5,3,16); assert(displays==8 && display_test_mode(runs)==0);
   assert(display_test_counts[0]==6 && display_test_counts[1]==2 && display_test_counts[2]==2);
   assert(display_test_save());
   video(NULL,5,3,16);
   video_release();
   assert(allocs == 1 && frees == 1 && waits == 3 && closes == 1 && displays == 8);
   assert(!video_pool && chunk_fd == -1);
   printf("PASS recovered chunk ioctl ABI, packed RGB565 rows, alternating buffers, prior-frame retention, wait-before-free\n");
   puts("PASS display comparison: unchanged held buffer, black packed pixels, two cycles, automatic permanent normal-video return");
   if (logfile) fclose(logfile);
   return 0;
}
