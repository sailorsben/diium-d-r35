/* Private readable reconstruction of D0/3DB2..3DFE, from the byte-matched ROM.
 * These named engine interfaces document the script's semantics. frame() yields
 * to the game's animation scheduler; it does not stop SPC/APU execution or sleep
 * the host. The low-level bank C maps expose the original handlers underneath. */
#include "ff6-bio-blast-model.h"
typedef struct FF6Animation FF6Animation;
void begin_bg1_script(FF6Animation *);
void move_bg1_here(FF6Animation *);
void play_attack_sound(FF6Animation *);
void sprite_priority(FF6Animation *,unsigned);
void magitek_action(FF6Animation *,unsigned);
void fixed_draw_order(FF6Animation *);
void normal_draw_order(FF6Animation *);
void init_circle(FF6Animation *,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned);
void move_circle_to_attacker(FF6Animation *);
void move_circle(FF6Animation *,int,int);
void zoom_circle(FF6Animation *,unsigned);
void update_circle(FF6Animation *);
void set_bg1_scroll_hdma(FF6Animation *,unsigned);
void init_bg1_scroll_wave(FF6Animation *,unsigned,unsigned,unsigned);
void update_bg1_scroll_wave(FF6Animation *);
void reset_bg1_scroll_hdma(FF6Animation *);
void set_bg1_palette_white_subtraction(FF6Animation *,unsigned);
void increment_bg1_palette_white_subtraction(FF6Animation *);
void frame(FF6Animation *,unsigned);
void hide_bg1_thread(FF6Animation *);
void end_animation(FF6Animation *);

void ff6_bio_blast_bg1(FF6Animation *animation)
{
    begin_bg1_script(animation);
    move_bg1_here(animation);
    play_attack_sound(animation);
    sprite_priority(animation,2);
    magitek_action(animation,2);
    fixed_draw_order(animation);
    init_circle(animation,128,75,4,222,255,127,32);
    move_circle_to_attacker(animation);
    move_circle(animation,-32,16);
    set_bg1_scroll_hdma(animation,6); /* repeated 32-line table */
    init_bg1_scroll_wave(animation,0,8,1); /* horizontal */
    init_bg1_scroll_wave(animation,1,2,2); /* vertical */
    frame(animation,0);
    hide_bg1_thread(animation);
    for(unsigned n=0;n<56;n++) {
        move_circle(animation,-2,0);
        zoom_circle(animation,2);
        update_circle(animation);
        update_bg1_scroll_wave(animation);
        frame(animation,0);
    }
    set_bg1_palette_white_subtraction(animation,0);
    for(unsigned n=0;n<33;n++) {
        increment_bg1_palette_white_subtraction(animation);
        zoom_circle(animation,1);
        update_circle(animation);
        update_bg1_scroll_wave(animation);
        frame(animation,0);
    }
    reset_bg1_scroll_hdma(animation);
    set_bg1_scroll_hdma(animation,3);
    normal_draw_order(animation);
    magitek_action(animation,0);
    end_animation(animation);
}
