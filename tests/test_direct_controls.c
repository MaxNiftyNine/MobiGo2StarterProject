#include <assert.h>
#include <string.h>

#include "mobigo_sdk/direct_controls.h"
#include "mobigo_sdk/resident_backend.h"

static mg_sdk_u16 matrix_keys;
static mg_sdk_u16 saved_volume = 3;
static mg_sdk_u16 saved_brightness = 1;
static mg_sdk_u16 applied_gain;
static mg_sdk_u16 applied_backlight;
static int poweroff_requests;
static int watchdog_kicks;
static int matrix_initialized;

void mg_sdk_matrix_init(void)
{
    ++matrix_initialized;
}

void mg_sdk_matrix_scan(struct mg_sdk_matrix_state *state)
{
    memset(state, 0, sizeof(*state));
    if (matrix_keys & MG_SDK_KEY_OFF) state->row[3] |= 1u << 2;
    if (matrix_keys & MG_SDK_KEY_BRIGHTNESS) state->row[4] |= 1u << 6;
    if (matrix_keys & MG_SDK_KEY_VOLUME_DOWN) state->row[4] |= 1u << 7;
    if (matrix_keys & MG_SDK_KEY_VOLUME_UP) state->row[4] |= 1u << 8;
}

mg_sdk_u16 mg_sdk_matrix_system_keys(
    const struct mg_sdk_matrix_state *state)
{
    mg_sdk_u16 keys = 0;
    if (state->row[3] & (1u << 2)) keys |= MG_SDK_KEY_OFF;
    if (state->row[4] & (1u << 6)) keys |= MG_SDK_KEY_BRIGHTNESS;
    if (state->row[4] & (1u << 7)) keys |= MG_SDK_KEY_VOLUME_DOWN;
    if (state->row[4] & (1u << 8)) keys |= MG_SDK_KEY_VOLUME_UP;
    return keys;
}

void mg_sdk_watchdog_kick(void)
{
    ++watchdog_kicks;
}

static int fake_load_volume(void *user, mg_sdk_u16 *level)
{
    (void)user;
    *level = saved_volume;
    return 1;
}

static void fake_save_volume(void *user, mg_sdk_u16 level)
{
    (void)user;
    saved_volume = level;
}

static void fake_apply_gain(void *user, mg_sdk_u16 gain)
{
    (void)user;
    applied_gain = gain;
}

static int fake_load_brightness(void *user, mg_sdk_u16 *level)
{
    (void)user;
    *level = saved_brightness;
    return 1;
}

static void fake_save_brightness(void *user, mg_sdk_u16 level)
{
    (void)user;
    saved_brightness = level;
}

static void fake_apply_backlight(void *user, mg_sdk_u16 value)
{
    (void)user;
    applied_backlight = value;
}

static void fake_poweroff(void *user)
{
    (void)user;
    ++poweroff_requests;
}

const struct mg_sdk_system_backend mg_sdk_experimental_resident_backend = {
    0,
    fake_load_volume,
    fake_save_volume,
    fake_apply_gain,
    fake_load_brightness,
    fake_save_brightness,
    fake_apply_backlight,
    0,
    0,
    0,
    0,
    0,
    fake_poweroff
};

int main(void)
{
    struct mg_sdk_direct_controls controls;

    assert(mg_sdk_direct_controls_init(&controls));
    assert(matrix_initialized == 1);
    assert(applied_gain == mg_sdk_volume_gain_table[3]);
    assert(applied_backlight == mg_sdk_backlight_table[1]);

    matrix_keys = MG_SDK_KEY_VOLUME_UP;
    mg_sdk_direct_controls_poll(&controls);
    assert(saved_volume == 4);
    assert(applied_gain == mg_sdk_volume_gain_table[4]);

    /* A held matrix cell is one edge, not auto-repeat every frame. */
    mg_sdk_direct_controls_poll(&controls);
    assert(saved_volume == 4);
    matrix_keys = 0;
    mg_sdk_direct_controls_poll(&controls);

    matrix_keys = MG_SDK_KEY_BRIGHTNESS;
    mg_sdk_direct_controls_poll(&controls);
    assert(saved_brightness == 2);
    assert(applied_backlight == mg_sdk_backlight_table[2]);
    matrix_keys = 0;
    mg_sdk_direct_controls_poll(&controls);

    matrix_keys = MG_SDK_KEY_OFF;
    mg_sdk_direct_controls_poll(&controls);
    assert(poweroff_requests == 1);
    assert(watchdog_kicks == 6);
    mg_sdk_direct_controls_hide(&controls);
    return 0;
}
