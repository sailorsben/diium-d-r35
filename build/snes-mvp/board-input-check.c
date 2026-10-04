/* Drive the actual GPIO decoder with vendor pin fixtures, not menu stubs. */
#define ioctl fixture_ioctl
#include "board.c"
#undef ioctl
#include <assert.h>
#include <libretro.h>
#include "vendor-input-reference.h"
static uint32_t low_pin=UINT32_MAX, second_low=UINT32_MAX;
static int read_failure;
int fixture_ioctl(int fd,unsigned long request,...)
{
    va_list args; struct gpio_request *r;
    assert(fd==42 && request==GPIO_READ);
    va_start(args,request); r=va_arg(args,struct gpio_request *); va_end(args);
    assert(r && r->reserved==0 && r->value==1);
    if(read_failure) { errno=EIO; return -1; }
    r->value=(r->pin==low_pin || r->pin==second_low)?0:1;
    return 0;
}
void startup_note(const char *format,...) { (void)format; }
int platform_heartbeat_open(void) { return 0; }
void platform_heartbeat_tick(void) {}
void platform_heartbeat_close(void) {}
int main(void)
{
    /* Raw GPIO->native masks from stock ReadJoystick 0x1599c. Expected
     * libretro IDs come from the executable's extracted callback table,
     * not a second copy of our interpreted physical direction names. */
    static const struct { uint32_t pin,native_mask; } gold[]={
        {0x200,0x10}, {0x201,0x40}, {0x202,0x80}, {0x203,0x20},
        {0x204,0x2000}, {0x205,0x4000}, {0x30b,0x8000}, {0x30d,0x1000},
        {0x30f,0x1}, {0x30c,0x8}, {0x30a,0x400}, {0x208,0x800},
        {0x207,0x100}, {0x30e,0x200}
    };
    size_t i;
    b.gpio_fd=42; b.null_backend=0; b.mixer_fd=-1;
    assert(!board_poll_input());
    for(i=0;i<sizeof(gold)/sizeof(gold[0]);i++) {
        unsigned id; uint32_t expected=0;
        for(id=0;id<16;id++)
            if(vendor_native_masks[id]&gold[i].native_mask) expected|=1u<<id;
        low_pin=gold[i].pin;
        assert(expected && board_poll_input()==expected);
    }
    low_pin=0x201; second_low=0x202;
    assert(board_poll_input()==((1u<<RETRO_DEVICE_ID_JOYPAD_DOWN)|(1u<<RETRO_DEVICE_ID_JOYPAD_LEFT)));
    second_low=UINT32_MAX;
    low_pin=0x206; assert(board_poll_input()==BOARD_MENU);
    low_pin=0x30f; second_low=0x30c; assert(board_poll_input()==BOARD_MENU);
    second_low=UINT32_MAX; read_failure=1; assert(!board_poll_input());
    puts("PASS: actual board GPIO decoder matches vendor D-pad/face pins, menu chord and failed-read behavior");
    return 0;
}
