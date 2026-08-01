#include "mobigo_sdk/input.h"

static const mg_sdk_u16 game_masks[] = {
    MG_SDK_GAME_KEY_LEFT,
    MG_SDK_GAME_KEY_RIGHT,
    MG_SDK_GAME_KEY_UP,
    MG_SDK_GAME_KEY_DOWN,
    MG_SDK_GAME_KEY_PRIMARY,
    MG_SDK_GAME_KEY_EXIT,
    MG_SDK_GAME_KEY_HELP
};

static void input_post(
    struct mg_sdk_input_pump *pump,
    mg_sdk_u16 code,
    mg_sdk_u16 kind)
{
    struct mg_sdk_input_event event;
    if (pump->backend->post_event == 0) {
        return;
    }
    event.code = code;
    event.kind = kind;
    event.x = -1;
    event.y = -1;
    pump->backend->post_event(pump->user, &event);
}

static int input_active(
    int (*callback)(void *, mg_sdk_u16),
    void *user,
    mg_sdk_u16 code)
{
    return callback != 0 && callback(user, code) != 0;
}

static void input_poll_special(
    struct mg_sdk_input_pump *pump,
    mg_sdk_u16 code,
    mg_sdk_u16 latch_mask)
{
    if (input_active(
            pump->backend->special_code_active,
            pump->user,
            code)) {
        if ((pump->special_latch & latch_mask) == 0) {
            input_post(pump, code, MG_SDK_INPUT_KEYBOARD);
        }
        pump->special_latch |= latch_mask;
    }
    else {
        pump->special_latch &= (mg_sdk_u16)~latch_mask;
    }
}

void mg_sdk_input_init(
    struct mg_sdk_input_pump *pump,
    const struct mg_sdk_input_backend *backend,
    void *user)
{
    if (pump == 0) {
        return;
    }
    pump->backend = backend;
    pump->user = user;
    pump->special_latch = 0;
}

void mg_sdk_input_poll(struct mg_sdk_input_pump *pump)
{
    mg_sdk_u16 code;
    unsigned int index;

    if (pump == 0 || pump->backend == 0) {
        return;
    }

    if (pump->backend->first_buffered_code != 0 &&
        pump->backend->first_buffered_code(pump->user, &code) != 0) {
        input_post(
            pump,
            (mg_sdk_u16)(code & 0x00ff),
            MG_SDK_INPUT_KEYBOARD);
    }

    input_poll_special(pump, MG_SDK_SPECIAL_CODE_90, 0x0001);
    input_poll_special(pump, MG_SDK_SPECIAL_CODE_14, 0x0002);

    for (index = 0;
         index < sizeof(game_masks) / sizeof(game_masks[0]);
         index++) {
        if (input_active(
                pump->backend->game_key_pressed_edge,
                pump->user,
                game_masks[index])) {
            input_post(
                pump,
                game_masks[index],
                MG_SDK_INPUT_GAME_CONTROL);
        }
    }

    if (input_active(
            pump->backend->system_key_pressed_edge,
            pump->user,
            MG_SDK_KEY_OFF)) {
        input_post(pump, MG_SDK_KEY_OFF, MG_SDK_INPUT_SYSTEM_KEY);
    }
}
