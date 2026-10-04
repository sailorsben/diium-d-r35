#ifndef D35_MVP_STARTUP_H
#define D35_MVP_STARTUP_H
void startup_begin(void);
void startup_note(const char *format, ...);
void startup_ready(void);
void startup_end(void);
#endif
