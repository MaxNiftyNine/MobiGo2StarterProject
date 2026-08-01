#ifndef MOBIGO_SDK_INPUT_H
#define MOBIGO_SDK_INPUT_H

#include "mobigo_sdk/system_controls.h"

enum mg_sdk_input_kind {
    MG_SDK_INPUT_KEYBOARD = 2,
    MG_SDK_INPUT_GAME_CONTROL = 3,
    MG_SDK_INPUT_SYSTEM_KEY = 4
};

enum mg_sdk_game_key_mask {
    MG_SDK_GAME_KEY_UP = 0x0001,
    MG_SDK_GAME_KEY_DOWN = 0x0002,
    MG_SDK_GAME_KEY_LEFT = 0x0004,
    MG_SDK_GAME_KEY_RIGHT = 0x0008,
    MG_SDK_GAME_KEY_PRIMARY = 0x0010,
    MG_SDK_GAME_KEY_EXIT = 0x0020,
    MG_SDK_GAME_KEY_HELP = 0x0040
};

/* Compatibility aliases for code written before the physical mapping was
 * recovered from the resident three-word key-map records. */
#define MG_SDK_GAME_KEY_01 MG_SDK_GAME_KEY_UP
#define MG_SDK_GAME_KEY_02 MG_SDK_GAME_KEY_DOWN
#define MG_SDK_GAME_KEY_04 MG_SDK_GAME_KEY_LEFT
#define MG_SDK_GAME_KEY_08 MG_SDK_GAME_KEY_RIGHT
#define MG_SDK_GAME_KEY_10 MG_SDK_GAME_KEY_PRIMARY
#define MG_SDK_GAME_KEY_20 MG_SDK_GAME_KEY_EXIT
#define MG_SDK_GAME_KEY_40 MG_SDK_GAME_KEY_HELP

enum mg_sdk_special_input_code {
    MG_SDK_SPECIAL_CODE_14 = 0x0014,
    MG_SDK_SPECIAL_CODE_90 = 0x0090
};

struct mg_sdk_input_event {
    mg_sdk_u16 code;
    mg_sdk_u16 kind;
    int x;
    int y;
};

struct mg_sdk_input_backend {
    int (*first_buffered_code)(void *user, mg_sdk_u16 *code);
    int (*special_code_active)(void *user, mg_sdk_u16 code);
    int (*game_key_pressed_edge)(void *user, mg_sdk_u16 mask);
    int (*system_key_pressed_edge)(void *user, mg_sdk_u16 mask);
    void (*post_event)(
        void *user,
        const struct mg_sdk_input_event *event);
};

struct mg_sdk_input_pump {
    const struct mg_sdk_input_backend *backend;
    void *user;
    mg_sdk_u16 special_latch;
};

void mg_sdk_input_init(
    struct mg_sdk_input_pump *pump,
    const struct mg_sdk_input_backend *backend,
    void *user);

void mg_sdk_input_poll(struct mg_sdk_input_pump *pump);

#endif
