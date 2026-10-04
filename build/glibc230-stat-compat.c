#define _GNU_SOURCE
#include <sys/stat.h>

/* ARM32's glibc 2.30 uses the versioned stat entry points. New toolchain
 * headers call the later unversioned functions. Keep the ARM32 time/off_t
 * ABI and bridge only those names; do not replace the device's libc. */
extern int __xstat(int, const char *, struct stat *);
extern int __fxstat(int, int, struct stat *);
extern int __fxstatat(int, int, const char *, struct stat *, int);
int stat(const char *path, struct stat *s) { return __xstat(3, path, s); }
int fstat(int fd, struct stat *s) { return __fxstat(3, fd, s); }
int fstatat(int fd, const char *path, struct stat *s, int flags)
{ return __fxstatat(3, fd, path, s, flags); }
