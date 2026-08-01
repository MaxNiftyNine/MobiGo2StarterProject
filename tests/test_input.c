#include <assert.h>
#include <stddef.h>

#include "mobigo_sdk/input.h"

enum { MAX_EVENTS = 32 };

struct fixture {
    mg_sdk_u16 buffered_code;
    int buffered;
    int special_14;
    int special_90;
    mg_sdk_u16 game;
    mg_sdk_u16 system;
    struct mg_sdk_input_event events[MAX_EVENTS];
    unsigned int event_count;
};

static int first_code(void *user, mg_sdk_u16 *code)
{
    struct fixture *fixture = user;
    if (!fixture->buffered) {
        return 0;
    }
    *code = fixture->buffered_code;
    return 1;
}

static int special_active(void *user, mg_sdk_u16 code)
{
    struct fixture *fixture = user;
    if (code == MG_SDK_SPECIAL_CODE_14) {
        return fixture->special_14;
    }
    if (code == MG_SDK_SPECIAL_CODE_90) {
        return fixture->special_90;
    }
    return 0;
}

static int game_pressed_edge(void *user, mg_sdk_u16 code)
{
    struct fixture *fixture = user;
    return (fixture->game & code) != 0;
}

static int system_pressed_edge(void *user, mg_sdk_u16 code)
{
    struct fixture *fixture = user;
    return (fixture->system & code) != 0;
}

static void post_event(
    void *user,
    const struct mg_sdk_input_event *event)
{
    struct fixture *fixture = user;
    assert(fixture->event_count < MAX_EVENTS);
    fixture->events[fixture->event_count++] = *event;
}

static const struct mg_sdk_input_backend backend = {
    first_code,
    special_active,
    game_pressed_edge,
    system_pressed_edge,
    post_event
};

static void test_all_sources_and_order(void)
{
    struct fixture fixture = {0};
    struct mg_sdk_input_pump pump;
    static const mg_sdk_u16 expected_codes[] = {
        0x00cd,
        0x0090,
        0x0014,
        0x0004,
        0x0008,
        0x0001,
        0x0002,
        0x0010,
        0x0020,
        0x0040,
        0x0200
    };
    unsigned int index;

    fixture.buffered = 1;
    fixture.buffered_code = 0xabcd;
    fixture.special_14 = 1;
    fixture.special_90 = 1;
    fixture.game =
        MG_SDK_GAME_KEY_UP |
        MG_SDK_GAME_KEY_DOWN |
        MG_SDK_GAME_KEY_LEFT |
        MG_SDK_GAME_KEY_RIGHT |
        MG_SDK_GAME_KEY_PRIMARY |
        MG_SDK_GAME_KEY_EXIT |
        MG_SDK_GAME_KEY_HELP;
    fixture.system = 0x0200;
    mg_sdk_input_init(&pump, &backend, &fixture);
    mg_sdk_input_poll(&pump);

    assert(fixture.event_count ==
        sizeof(expected_codes) / sizeof(expected_codes[0]));
    for (index = 0; index < fixture.event_count; index++) {
        assert(fixture.events[index].code == expected_codes[index]);
        assert(fixture.events[index].x == -1);
        assert(fixture.events[index].y == -1);
    }
    assert(fixture.events[0].kind == MG_SDK_INPUT_KEYBOARD);
    assert(fixture.events[1].kind == MG_SDK_INPUT_KEYBOARD);
    assert(fixture.events[2].kind == MG_SDK_INPUT_KEYBOARD);
    assert(fixture.events[3].kind == MG_SDK_INPUT_GAME_CONTROL);
    assert(fixture.events[10].kind == MG_SDK_INPUT_SYSTEM_KEY);
}

static void test_special_codes_are_rising_edge(void)
{
    struct fixture fixture = {0};
    struct mg_sdk_input_pump pump;

    mg_sdk_input_init(&pump, &backend, &fixture);
    fixture.special_90 = 1;
    mg_sdk_input_poll(&pump);
    mg_sdk_input_poll(&pump);
    assert(fixture.event_count == 1);

    fixture.special_90 = 0;
    mg_sdk_input_poll(&pump);
    fixture.special_90 = 1;
    mg_sdk_input_poll(&pump);
    assert(fixture.event_count == 2);
}

int main(void)
{
    test_all_sources_and_order();
    test_special_codes_are_rising_edge();
    return 0;
}
