#include "ui.h"

/* A compact, hand-authored 5 x 7 bitmap alphabet; row bits run left to right.
 * The UI deliberately needs no font library, image decode, or heap allocation. */
struct glyph { unsigned char c, row[7]; };
static const struct glyph alphabet[] = {
 {'A',{14,17,17,31,17,17,17}}, {'B',{30,17,17,30,17,17,30}},
 {'C',{14,17,16,16,16,17,14}}, {'D',{30,17,17,17,17,17,30}},
 {'E',{31,16,16,30,16,16,31}}, {'F',{31,16,16,30,16,16,16}},
 {'G',{14,17,16,23,17,17,15}}, {'H',{17,17,17,31,17,17,17}},
 {'I',{14,4,4,4,4,4,14}}, {'J',{7,2,2,2,18,18,12}},
 {'K',{17,18,20,24,20,18,17}}, {'L',{16,16,16,16,16,16,31}},
 {'M',{17,27,21,21,17,17,17}}, {'N',{17,25,21,19,17,17,17}},
 {'O',{14,17,17,17,17,17,14}}, {'P',{30,17,17,30,16,16,16}},
 {'Q',{14,17,17,17,21,18,13}}, {'R',{30,17,17,30,20,18,17}},
 {'S',{15,16,16,14,1,1,30}}, {'T',{31,4,4,4,4,4,4}},
 {'U',{17,17,17,17,17,17,14}}, {'V',{17,17,17,17,17,10,4}},
 {'W',{17,17,17,21,21,21,10}}, {'X',{17,17,10,4,10,17,17}},
 {'Y',{17,17,10,4,4,4,4}}, {'Z',{31,1,2,4,8,16,31}},
 {'a',{0,0,14,1,15,17,15}}, {'b',{16,16,22,25,17,17,30}},
 {'c',{0,0,14,17,16,17,14}}, {'d',{1,1,13,19,17,17,15}},
 {'e',{0,0,14,17,31,16,14}}, {'f',{6,9,8,28,8,8,8}},
 {'g',{0,0,15,17,15,1,14}}, {'h',{16,16,22,25,17,17,17}},
 {'i',{4,0,12,4,4,4,14}}, {'j',{2,0,6,2,2,18,12}},
 {'k',{16,16,18,20,24,20,18}}, {'l',{12,4,4,4,4,4,14}},
 {'m',{0,0,26,21,21,21,21}}, {'n',{0,0,22,25,17,17,17}},
 {'o',{0,0,14,17,17,17,14}}, {'p',{0,0,30,17,30,16,16}},
 {'q',{0,0,15,17,15,1,1}}, {'r',{0,0,22,25,16,16,16}},
 {'s',{0,0,15,16,14,1,30}}, {'t',{8,8,28,8,8,9,6}},
 {'u',{0,0,17,17,17,19,13}}, {'v',{0,0,17,17,17,10,4}},
 {'w',{0,0,17,17,21,21,10}}, {'x',{0,0,17,10,4,10,17}},
 {'y',{0,0,17,17,15,1,14}}, {'z',{0,0,31,2,4,8,31}},
 {'0',{14,17,19,21,25,17,14}}, {'1',{4,12,4,4,4,4,14}},
 {'2',{14,17,1,2,4,8,31}}, {'3',{30,1,1,14,1,1,30}},
 {'4',{2,6,10,18,31,2,2}}, {'5',{31,16,16,30,1,1,30}},
 {'6',{14,16,16,30,17,17,14}}, {'7',{31,1,2,4,8,8,8}},
 {'8',{14,17,17,14,17,17,14}}, {'9',{14,17,17,15,1,1,14}},
 {' ',{0,0,0,0,0,0,0}}, {'.',{0,0,0,0,0,6,6}},
 {',',{0,0,0,0,6,6,4}}, {':',{0,6,6,0,6,6,0}},
 {';',{0,6,6,0,6,6,4}}, {'!',{4,4,4,4,4,0,4}},
 {'?',{14,17,1,2,4,0,4}}, {'-',{0,0,0,31,0,0,0}},
 {'_',{0,0,0,0,0,0,31}}, {'/',{1,2,2,4,8,8,16}},
 {'\\',{16,8,8,4,2,2,1}}, {'(',{2,4,8,8,8,4,2}},
 {')',{8,4,2,2,2,4,8}}, {'[',{14,8,8,8,8,8,14}},
 {']',{14,2,2,2,2,2,14}}, {'+',{0,4,4,31,4,4,0}},
 {'=',{0,0,31,0,31,0,0}}, {'&',{12,18,20,8,21,18,13}},
 {'\'',{4,4,2,0,0,0,0}}, {'"',{10,10,5,0,0,0,0}},
 {'#',{10,10,31,10,31,10,10}}, {'%',{25,25,2,4,8,19,19}},
 {'@',{14,17,23,21,23,16,14}}, {'>',{16,8,4,2,4,8,16}},
 {'<',{1,2,4,8,4,2,1}}, {'*',{0,21,14,31,14,21,0}},
 {'|',{4,4,4,4,4,4,4}}, {'~',{0,0,9,22,0,0,0}}
};

struct canvas { uint16_t *pixels; unsigned pitch; };
#define RGB(r,g,b) ((uint16_t)((((r) >> 3) << 11) | (((g) >> 2) << 5) | ((b) >> 3)))
static const uint16_t bg = RGB(9,20,30);
static const uint16_t panel = RGB(16,33,44);
static const uint16_t line = RGB(32,58,68);
static const uint16_t ink = RGB(242,240,226);
static const uint16_t muted = RGB(150,174,181);
static const uint16_t accent = RGB(92,216,196);
static const uint16_t selected_bg = RGB(22,80,82);

static void rect(struct canvas c, int x, int y, int w, int h, uint16_t color)
{
    int yy, xx;
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > (int)UI_WIDTH) w = (int)UI_WIDTH - x;
    if (y + h > (int)UI_HEIGHT) h = (int)UI_HEIGHT - y;
    if (w <= 0 || h <= 0) return;
    for (yy = y; yy < y+h; ++yy) {
        uint16_t *row = c.pixels + (size_t)yy * c.pitch + x;
        for (xx = 0; xx < w; ++xx) row[xx] = color;
    }
}

/* Consume one UTF-8 sequence safely. Unsupported glyphs become one '?' rather
 * than one glyph per byte. Filenames are only displayed; never modified. */
static unsigned char next_char(const char **s)
{
    unsigned char ch = (unsigned char)*(*s)++;
    if (ch >= 128) {
        while ((**s & 0xc0) == 0x80) ++*s;
        return '?';
    }
    return ch < 32 ? ' ' : ch;
}

static void letter(struct canvas c, int x, int y, unsigned char ch,
                   unsigned scale, uint16_t color)
{
    size_t i;
    unsigned row, bit;
    const unsigned char *bits = NULL;
    for (i = 0; i < sizeof(alphabet)/sizeof(alphabet[0]); ++i)
        if (alphabet[i].c == ch) { bits = alphabet[i].row; break; }
    if (!bits) {
        letter(c,x,y,'?',scale,color);
        return;
    }
    for (row = 0; row < 7; ++row)
        for (bit = 0; bit < 5; ++bit)
            if (bits[row] & (16u >> bit))
                rect(c,x+(int)(bit*scale),y+(int)(row*scale),
                     (int)scale,(int)scale,color);
}

static void text(struct canvas c, int x, int y, const char *s,
                 unsigned scale, uint16_t color, unsigned max_columns)
{
    unsigned n = 0, length = 0;
    const char *p = s ? s : "";
    const char *q = p;
    if (!scale || !max_columns) return;
    while (*q && length <= max_columns) { next_char(&q); ++length; }
    while (*p && n < max_columns) {
        unsigned char ch = next_char(&p);
        if (length > max_columns && max_columns >= 3 && n >= max_columns-3)
            ch = '.';
        letter(c,x+(int)(n*6*scale),y,ch,scale,color);
        ++n;
    }
}

static void number(char out[24], size_t n)
{
    char reverse[24];
    unsigned count = 0, i;
    do { reverse[count++] = (char)('0' + n%10); n /= 10; }
    while (n && count < sizeof(reverse)-1);
    for (i = 0; i < count; ++i) out[i] = reverse[count-i-1];
    out[count] = '\0';
}

static void base(struct canvas c)
{
    rect(c,0,0,UI_WIDTH,UI_HEIGHT,bg);
    rect(c,28,24,4,14,accent);
    text(c,42,24,"SNES",2,accent,4);
}

static void footer(struct canvas c, const char *status, const char *hints)
{
    rect(c,28,407,584,1,line);
    text(c,28,421,status && *status ? status : "Ready to play.",2,muted,48);
    text(c,28,454,hints,2,ink,48);
}

void ui_draw_library(uint16_t *pixels, unsigned pitch_pixels,
                     const char *const *names, size_t count, size_t selected,
                     const char *status)
{
    struct canvas c = {pixels,pitch_pixels};
    size_t first = 0, end, i;
    char total[24], position[24];
    if (!pixels || pitch_pixels < UI_WIDTH) return;
    if (!names) count = 0;
    if (count && selected >= count) selected = count-1;
    base(c);
    text(c,28,58,"Game Library",3,ink,28);
    number(total,count);
    text(c,490,25,total,2,muted,9);
    text(c,490,45,count == 1 ? "game" : "games",1,muted,12);
    rect(c,28,96,584,1,line);
    if (!count) {
        text(c,64,181,"No SNES games found",3,ink,28);
        text(c,64,233,"Copy games to ROMs/SNES",2,muted,40);
        text(c,64,259,"Supported: .sfc  .smc  .zip",2,muted,40);
        footer(c,status,"D-PAD Move       A Play       B Back");
        return;
    }
    if (selected >= UI_LIBRARY_ROWS/2) first = selected-UI_LIBRARY_ROWS/2;
    if (count > UI_LIBRARY_ROWS && first > count-UI_LIBRARY_ROWS)
        first = count-UI_LIBRARY_ROWS;
    if (count <= UI_LIBRARY_ROWS) first = 0;
    end = first + UI_LIBRARY_ROWS;
    if (end > count) end = count;
    for (i = first; i < end; ++i) {
        int y = 110+(int)(i-first)*31;
        if (i == selected) {
            rect(c,22,y,580,29,selected_bg);
            rect(c,22,y,4,29,accent);
            text(c,36,y+7,">",2,accent,1);
        }
        text(c,59,y+7,names[i],2,i == selected ? ink : muted,44);
    }
    if (count > UI_LIBRARY_ROWS) {
        unsigned thumb = (unsigned)((UI_LIBRARY_ROWS*279u)/count);
        unsigned offset;
        if (thumb < 14) thumb = 14;
        offset = (unsigned)((first*(279u-thumb))/(count-UI_LIBRARY_ROWS));
        rect(c,611,110,3,279,line);
        rect(c,611,110+(int)offset,3,(int)thumb,accent);
    }
    number(position,selected+1);
    text(c,28,389,position,1,accent,20);
    text(c,90,389,"selected",1,muted,12);
    footer(c,status,"D-PAD Move       A Play       B Back");
}

void ui_draw_pause(uint16_t *pixels, unsigned pitch_pixels,
                   const char *game_name, unsigned selected, const char *status)
{
    static const char *const options[UI_PAUSE_COUNT] = {
        "Resume game", "Save snapshot", "Load snapshot", "Exit game"
    };
    struct canvas c = {pixels,pitch_pixels};
    unsigned i;
    if (!pixels || pitch_pixels < UI_WIDTH) return;
    if (selected >= UI_PAUSE_COUNT) selected = 0;
    base(c);
    text(c,28,58,"Paused",3,ink,28);
    text(c,28,98,game_name,2,muted,48);
    for (i = 0; i < UI_PAUSE_COUNT; ++i) {
        int y = 145+(int)i*54;
        rect(c,104,y,432,45,i == selected ? selected_bg : panel);
        if (i == selected) {
            rect(c,104,y,4,45,accent);
            text(c,122,y+16,">",2,accent,1);
        }
        text(c,151,y+16,options[i],2,i == selected ? ink : muted,29);
    }
    footer(c,status,"D-PAD Move       A Choose     B Resume");
}

void ui_draw_notice(uint16_t *pixels, unsigned pitch_pixels,
                    const char *title, const char *message)
{
    struct canvas c = {pixels,pitch_pixels};
    if (!pixels || pitch_pixels < UI_WIDTH) return;
    base(c);
    rect(c,28,124,584,222,panel);
    rect(c,28,124,4,222,accent);
    text(c,53,163,title ? title : "SNES",3,ink,30);
    text(c,53,221,message ? message : "",2,muted,44);
}
