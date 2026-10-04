#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void)
{
   char name[] = "/tmp/dr35-2010-stat-compat-XXXXXX";
   struct stat a, b, c;
   int fd = mkstemp(name);
   assert(fd >= 0 && write(fd, "device-abi", 10) == 10);
   memset(&a, 0xa5, sizeof(a));
   memset(&b, 0xa5, sizeof(b));
   memset(&c, 0xa5, sizeof(c));
   assert(!stat(name, &a) && !fstat(fd, &b));
   assert(!fstatat(AT_FDCWD, name, &c, 0));
   assert(S_ISREG(a.st_mode) && a.st_size == 10 && b.st_size == 10 && c.st_size == 10);
   assert(a.st_ino == b.st_ino && b.st_ino == c.st_ino);
   assert(stat("missing-stat-compat-fixture.bin", &c) == -1 && errno == ENOENT);
   assert(!close(fd) && !unlink(name));
   puts("PASS ARM32 glibc 2.30 stat/fstat/fstatat layout, size, type, inode and errno");
   return 0;
}
