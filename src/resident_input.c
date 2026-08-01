#include "mobigo_sdk/resident_input.h"
#include "mobigo_sdk/resident_addresses.h"

typedef const mg_sdk_u16 *(*resident_get_input_pointer_fn)(void);
typedef mg_sdk_u16 (*resident_get_input_count_fn)(void);
typedef int (*resident_test_input_fn)(mg_sdk_u16 code);
typedef void (*resident_post_framework_event_fn)(
    mg_sdk_u16 event_id,
    int route_a,
    int route_b,
    int route_c,
    int route_d,
    mg_sdk_u16 code,
    mg_sdk_u16 kind,
    int x,
    int y);

#define RESIDENT_GET_INPUT_POINTER \
    ((resident_get_input_pointer_fn)MG_SDK_RESIDENT_GET_INPUT_EVENT_PTR)
#define RESIDENT_GET_INPUT_COUNT \
    ((resident_get_input_count_fn)MG_SDK_RESIDENT_GET_INPUT_EVENT_COUNT)
#define RESIDENT_TEST_SPECIAL_KEY \
    ((resident_test_input_fn)MG_SDK_RESIDENT_TEST_SPECIAL_KEY)
#define RESIDENT_GAME_KEY_PRESSED \
    ((resident_test_input_fn)MG_SDK_RESIDENT_GAME_KEY_PRESSED)
#define RESIDENT_SYSTEM_KEY_PRESSED \
    ((resident_test_input_fn)MG_SDK_RESIDENT_SYSTEM_KEY_PRESSED)
#define RESIDENT_POST_FRAMEWORK_EVENT \
    ((resident_post_framework_event_fn)MG_SDK_RESIDENT_POST_FRAMEWORK_EVENT)

static int resident_first_buffered_code(
    void *user,
    mg_sdk_u16 *code)
{
    const mg_sdk_u16 *events;
    (void)user;
    if (RESIDENT_GET_INPUT_COUNT() == 0) {
        return 0;
    }
    events = RESIDENT_GET_INPUT_POINTER();
    *code = events[0];
    return 1;
}

static int resident_special_code_active(void *user, mg_sdk_u16 code)
{
    (void)user;
    return RESIDENT_TEST_SPECIAL_KEY(code);
}

static int resident_game_key_pressed_edge(void *user, mg_sdk_u16 mask)
{
    (void)user;
    return RESIDENT_GAME_KEY_PRESSED(mask);
}

static int resident_system_key_pressed_edge(void *user, mg_sdk_u16 mask)
{
    (void)user;
    return RESIDENT_SYSTEM_KEY_PRESSED(mask);
}

static void resident_post_event(
    void *user,
    const struct mg_sdk_input_event *event)
{
    (void)user;
    RESIDENT_POST_FRAMEWORK_EVENT(
        0x1005,
        -1,
        -1,
        -2,
        -1,
        event->code,
        event->kind,
        event->x,
        event->y);
}

const struct mg_sdk_input_backend
    mg_sdk_experimental_resident_input_backend = {
        resident_first_buffered_code,
        resident_special_code_active,
        resident_game_key_pressed_edge,
        resident_system_key_pressed_edge,
        resident_post_event
    };
