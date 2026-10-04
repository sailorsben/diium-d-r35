#ifndef D35_MVP_RUNNER_H
#define D35_MVP_RUNNER_H

enum runner_menu_action {
    RUNNER_RESUME = 0,
    RUNNER_SAVE_STATE = 1,
    RUNNER_LOAD_STATE = 2,
    RUNNER_EXIT = 3,
    RUNNER_RESET = 4
};
typedef int (*runner_menu_callback)(void *userdata, const char *status);
void runner_set_menu_callback(runner_menu_callback callback, void *userdata);
void runner_set_initial_sram(const char *path);
void runner_request_stop(void);
const char *runner_last_error(void);
const char *runner_last_status(void);
int runner_run(const char *rom_path, const char *core_path, const char *save_dir);

#endif
