#include "mobigo_sdk/touch.h"

void mg_sdk_touch_poll(
    const struct mg_sdk_touch_backend *backend,
    void *backend_user,
    mg_sdk_touch_callback callback,
    void *callback_user)
{
    const mg_sdk_u16 *words;
    mg_sdk_u16 count;
    mg_sdk_u16 index;

    if (backend == 0 || backend->event_words == 0 ||
        backend->event_count == 0 || callback == 0) {
        return;
    }

    count = backend->event_count(backend_user);
    if (count == 0) {
        return;
    }
    words = backend->event_words(backend_user);
    if (words == 0) {
        return;
    }

    for (index = 0; index < count; index++) {
        const mg_sdk_u16 *record = words + (mg_sdk_u16)(index * 4);
        struct mg_sdk_touch_event event;
        event.x = (mg_sdk_s16)record[0];
        event.y = (mg_sdk_s16)record[1];
        event.state =
            event.x == (mg_sdk_s16)-1 || event.y == (mg_sdk_s16)-1
                ? MG_SDK_TOUCH_STATE_SENTINEL
                : MG_SDK_TOUCH_STATE_COORDINATE;
        event.raw_word_2 = record[2];
        event.raw_word_3 = record[3];
        callback(callback_user, &event);
    }
}
