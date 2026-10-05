#include <fcntl.h>
#include <stdint.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
int fixture(void) {
    uint32_t parameters[57]; int status=0,fd=open("/dev/pscaler_a",O_RDWR);
    memset(parameters,0,sizeof(parameters)); ((unsigned char *)parameters)[227]=0x5a;
    parameters[14]=0x1000; parameters[16]=0x2000; parameters[17]=0x3000;
    if(fd<0 || ioctl(fd,0x5003u)<0 || ioctl(fd,0x40e45000u,parameters)<0 ||
       ioctl(fd,0x80045001u,0)<0 || ioctl(fd,0x80045004u,3000)<0 ||
       ioctl(fd,0x80045005u,&status)<0 || status!=2 || ioctl(fd,0x5003u)<0 || close(fd)<0) return 1;
    return 0;
}
