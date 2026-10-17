/* Run the captured zImage's actual ARM decompressor, not Linux boot.
 * RAM only. Console output/error seams intercepted; no privileged head.S.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
static void error(const char *s){fprintf(stderr,"decompressor error: %s\n",s);exit(3);}
static void map(uintptr_t a,size_t n){void *p=mmap((void *)a,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(p==(void *)a);}
__attribute__((noinline)) static void patch(uintptr_t a,const void *p,size_t n){memcpy((void *)a,p,n);}
static size_t readfile(const char *name,void *p,size_t max){FILE *f=fopen(name,"rb");assert(f);size_t n=fread(p,1,max,f);assert(feof(f));assert(!fclose(f));return n;}
int main(int argc,char **argv){
 assert(argc==3);map(0,0x400000);map(0x02000000,0x800000);map(0x03000000,0x200000);
 size_t n=readfile(argv[1],(void *)0,0x400000);assert(n==0x241c98);
 uint32_t ret=0xe12fff1e;patch(0x930,&ret,4);
 uint32_t j[]={0xe51ff004,(uint32_t)(uintptr_t)error};patch(0x978,j,8);
 __builtin___clear_cache((void *)0,(void *)0x400000);
 ((void (*)(unsigned,unsigned,unsigned,unsigned))0x9ec)(0x02000000,0x03000000,0x03200000,0);
 unsigned char *expected=malloc(0x800000);assert(expected);size_t bytes=readfile(argv[2],expected,0x800000);assert(bytes==7476028);
 if(memcmp(expected,(void *)0x02000000,bytes)){fputs("decompressor output mismatch\n",stderr);free(expected);return 4;}free(expected);
 puts("PASS captured ARM zImage decompressor produces every expected kernel byte; privileged boot/kernel not executed");return 0;
}
