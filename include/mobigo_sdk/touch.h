#ifndef MOBIGO_SDK_TOUCH_H
#define MOBIGO_SDK_TOUCH_H

#include "mobigo_sdk/system_controls.h"

enum mg_sdk_touch_state {
    MG_SDK_TOUCH_STATE_COORDINATE = 0,
    MG_SDK_TOUCH_STATE_SENTINEL = 2
};

/*
 * The resident queue uses four 16-bit words per record. G1 consumes x and y,
 * derives state 2 when either coordinate is -1, and ignores the final two
 * words. They are preserved here for future cross-title identification.
 */
struct mg_sdk_touch_event {
    mg_sdk_s16 x;
    mg_sdk_s16 y;
    mg_sdk_u16 state;
    mg_sdk_u16 raw_word_2;
    mg_sdk_u16 raw_word_3;
};

struct mg_sdk_touch_backend {
    const mg_sdk_u16 *(*event_words)(void *user);
    mg_sdk_u16 (*event_count)(void *user);
};

typedef void (*mg_sdk_touch_callback)(
    void *user,
    const struct mg_sdk_touch_event *event);

void mg_sdk_touch_poll(
    const struct mg_sdk_touch_backend *backend,
    void *backend_user,
    mg_sdk_touch_callback callback,
    void *callback_user);

#endif
