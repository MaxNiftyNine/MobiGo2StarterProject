#include <assert.h>

#include "mobigo_sdk/touch.h"

struct fixture {
    mg_sdk_u16 words[12];
    mg_sdk_u16 count;
    struct mg_sdk_touch_event events[3];
    mg_sdk_u16 received;
};

static const mg_sdk_u16 *event_words(void *user)
{
    struct fixture *fixture = user;
    return fixture->words;
}

static mg_sdk_u16 event_count(void *user)
{
    struct fixture *fixture = user;
    return fixture->count;
}

static void receive_event(
    void *user,
    const struct mg_sdk_touch_event *event)
{
    struct fixture *fixture = user;
    assert(fixture->received < 3);
    fixture->events[fixture->received++] = *event;
}

static const struct mg_sdk_touch_backend backend = {
    event_words,
    event_count
};

static void test_records_and_sentinel(void)
{
    struct fixture fixture = {
        {
            120, 80, 0xaaaa, 0xbbbb,
            0xffff, 80, 0xcccc, 0xdddd,
            319, 239, 0x1111, 0x2222
        },
        3,
        {{0}},
        0
    };

    mg_sdk_touch_poll(
        &backend, &fixture, receive_event, &fixture);

    assert(fixture.received == 3);
    assert(fixture.events[0].x == 120);
    assert(fixture.events[0].y == 80);
    assert(fixture.events[0].state == MG_SDK_TOUCH_STATE_COORDINATE);
    assert(fixture.events[0].raw_word_2 == 0xaaaa);
    assert(fixture.events[0].raw_word_3 == 0xbbbb);
    assert(fixture.events[1].x == -1);
    assert(fixture.events[1].state == MG_SDK_TOUCH_STATE_SENTINEL);
    assert(fixture.events[2].x == 319);
    assert(fixture.events[2].y == 239);
}

static void test_empty_queue(void)
{
    struct fixture fixture = {{0}, 0, {{0}}, 0};
    mg_sdk_touch_poll(
        &backend, &fixture, receive_event, &fixture);
    assert(fixture.received == 0);
}

int main(void)
{
    test_records_and_sentinel();
    test_empty_queue();
    return 0;
}
