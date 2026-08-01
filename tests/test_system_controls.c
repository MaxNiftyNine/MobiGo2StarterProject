#include <assert.h>
#include <string.h>

#include "mobigo_sdk/system_controls.h"

struct fake_platform {
    mg_sdk_u16 edge;
    mg_sdk_u16 saved_volume;
    mg_sdk_u16 saved_brightness;
    mg_sdk_u16 gain;
    mg_sdk_u16 backlight;
    mg_sdk_u16 overlay_kind;
    mg_sdk_u16 overlay_level;
    mg_sdk_u16 overlay_x;
    mg_sdk_u16 overlay_y;
    mg_sdk_u16 hidden;
    mg_sdk_u16 feedback;
    mg_sdk_u16 feedback_is_active;
    mg_sdk_u16 powered_off;
    mg_sdk_u32 now;
};

static int key_edge(void *user, mg_sdk_u16 mask)
{
    struct fake_platform *fake = user;
    if ((fake->edge & mask) == 0) {
        return 0;
    }
    fake->edge &= (mg_sdk_u16)~mask;
    return 1;
}

static int load_volume(void *user, mg_sdk_u16 *level)
{
    *level = ((struct fake_platform *)user)->saved_volume;
    return 1;
}

static int load_brightness(void *user, mg_sdk_u16 *level)
{
    *level = ((struct fake_platform *)user)->saved_brightness;
    return 1;
}

static void save_volume(void *user, mg_sdk_u16 level)
{
    ((struct fake_platform *)user)->saved_volume = level;
}

static void save_brightness(void *user, mg_sdk_u16 level)
{
    ((struct fake_platform *)user)->saved_brightness = level;
}

static void apply_gain(void *user, mg_sdk_u16 value)
{
    ((struct fake_platform *)user)->gain = value;
}

static void apply_backlight(void *user, mg_sdk_u16 value)
{
    ((struct fake_platform *)user)->backlight = value;
}

static mg_sdk_u32 ticks(void *user)
{
    return ((struct fake_platform *)user)->now;
}

static void show_overlay(
    void *user,
    enum mg_sdk_overlay_kind kind,
    mg_sdk_u16 level,
    mg_sdk_u16 x,
    mg_sdk_u16 y)
{
    struct fake_platform *fake = user;
    fake->overlay_kind = (mg_sdk_u16)kind;
    fake->overlay_level = level;
    fake->overlay_x = x;
    fake->overlay_y = y;
    fake->hidden = 0;
}

static void hide_overlay(void *user)
{
    ((struct fake_platform *)user)->hidden = 1;
}

static int play_feedback(void *user, enum mg_sdk_feedback_kind kind)
{
    ((struct fake_platform *)user)->feedback = (mg_sdk_u16)kind;
    return 12;
}

static int feedback_active(void *user, int handle)
{
    assert(handle == 12);
    return ((struct fake_platform *)user)->feedback_is_active;
}

static void request_poweroff(void *user)
{
    ((struct fake_platform *)user)->powered_off++;
}

static const struct mg_sdk_system_backend backend = {
    key_edge,
    load_volume,
    save_volume,
    apply_gain,
    load_brightness,
    save_brightness,
    apply_backlight,
    ticks,
    show_overlay,
    hide_overlay,
    play_feedback,
    feedback_active,
    request_poweroff
};

int main(void)
{
    struct fake_platform fake;
    struct mg_sdk_system_controls controls;

    memset(&fake, 0, sizeof(fake));
    fake.saved_volume = 7;
    fake.saved_brightness = 2;
    mg_sdk_system_controls_init(&controls, &backend, &fake);
    assert(controls.volume == 7);
    assert(fake.gain == 79);
    assert(controls.brightness == 2);
    assert(fake.backlight == 10);

    fake.edge = MG_SDK_KEY_VOLUME_UP;
    mg_sdk_system_controls_poll(&controls);
    assert(controls.volume == 8);
    assert(fake.saved_volume == 8);
    assert(fake.gain == 91);
    assert(fake.overlay_kind == MG_SDK_OVERLAY_VOLUME);
    assert(fake.overlay_level == 8);
    assert(fake.overlay_x == 109 && fake.overlay_y == 214);

    fake.edge = MG_SDK_KEY_VOLUME_UP;
    mg_sdk_system_controls_poll(&controls);
    fake.edge = MG_SDK_KEY_VOLUME_UP;
    mg_sdk_system_controls_poll(&controls);
    assert(controls.volume == 9);
    assert(fake.feedback == MG_SDK_FEEDBACK_VOLUME_MAXIMUM);

    fake.edge = MG_SDK_KEY_BRIGHTNESS;
    mg_sdk_system_controls_poll(&controls);
    assert(controls.brightness == 3);
    assert(fake.backlight == 15);
    fake.edge = MG_SDK_KEY_BRIGHTNESS;
    mg_sdk_system_controls_poll(&controls);
    assert(controls.brightness == 0);
    assert(fake.backlight == 1);

    fake.now = controls.overlay_started + controls.overlay_ticks;
    mg_sdk_system_controls_poll(&controls);
    assert(controls.overlay_visible == 0);
    assert(fake.hidden == 1);

    fake.edge = MG_SDK_KEY_OFF;
    fake.feedback_is_active = 1;
    mg_sdk_system_controls_poll(&controls);
    assert(controls.poweroff_pending == 1);
    assert(fake.overlay_kind == MG_SDK_OVERLAY_POWEROFF);
    assert(fake.overlay_x == 160 && fake.overlay_y == 120);
    assert(fake.powered_off == 0);

    fake.feedback_is_active = 0;
    mg_sdk_system_controls_poll(&controls);
    assert(fake.powered_off == 1);

    return 0;
}
