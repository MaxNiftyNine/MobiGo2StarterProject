#include <assert.h>

#include "mobigo_sdk/resident_backend.h"
#include "mobigo_sdk/standard_controls.h"

static mg_sdk_u16 edge_keys;
static mg_sdk_u16 saved_volume = 4;
static mg_sdk_u16 saved_brightness = 1;
static mg_sdk_u16 applied_gain;
static mg_sdk_u16 applied_backlight;
static mg_sdk_u32 fake_ticks;
static int copy_count;
static int register_count;
static int settings_shows;
static int brightness_shows;
static int poweroff_shows;
static int settings_hides;
static int poweroff_hides;
static int poweroff_requests;
static int destroy_count;
static int fail_poweroff_create;
static int watchdog_kicks;

void mg_sdk_watchdog_kick(void)
{
    ++watchdog_kicks;
}

static int fake_key(void *user, mg_sdk_u16 mask)
{
    (void)user;
    return (edge_keys & mask) != 0;
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

static mg_sdk_u32 fake_get_ticks(void *user)
{
    (void)user;
    return fake_ticks;
}

static void fake_poweroff(void *user)
{
    (void)user;
    ++poweroff_requests;
}

const struct mg_sdk_system_backend mg_sdk_experimental_resident_backend = {
    fake_key,
    fake_load_volume,
    fake_save_volume,
    fake_apply_gain,
    fake_load_brightness,
    fake_save_brightness,
    fake_apply_backlight,
    fake_get_ticks,
    0,
    0,
    0,
    0,
    fake_poweroff
};

void mobigo_clean_system_ui_copy_bundle(unsigned short *destination)
{
    ++copy_count;
    destination[0] = 0x1234u;
}

void mobigo_clean_system_ui_register(unsigned short *writable_bundle)
{
    assert(writable_bundle[0] == 0x1234u);
    ++register_count;
}

mg_sdk_ui_handle mobigo_clean_system_ui_create_settings(void)
{
    return 0x80000000UL;
}

mg_sdk_ui_handle mobigo_clean_system_ui_create_poweroff(void)
{
    if (fail_poweroff_create) return MG_SDK_INVALID_UI_HANDLE;
    return 0x80000001UL;
}

void mobigo_clean_system_ui_show_brightness(
    mg_sdk_ui_handle handle, unsigned short level)
{
    assert(handle == 0x80000000UL);
    assert(level == saved_brightness);
    ++brightness_shows;
}

void mobigo_clean_system_ui_show_volume(
    mg_sdk_ui_handle handle, unsigned short level)
{
    assert(handle == 0x80000000UL);
    assert(level == saved_volume);
    ++settings_shows;
}

void mobigo_clean_system_ui_hide_settings(mg_sdk_ui_handle handle)
{
    assert(handle == 0x80000000UL);
    ++settings_hides;
}

void mobigo_clean_system_ui_show_poweroff(mg_sdk_ui_handle handle)
{
    assert(handle == 0x80000001UL);
    ++poweroff_shows;
}

void mobigo_clean_system_ui_hide_poweroff(mg_sdk_ui_handle handle)
{
    assert(handle == 0x80000001UL);
    ++poweroff_hides;
}

void mg_sdk_ui_b_destroy(mg_sdk_ui_handle handle)
{
    assert(handle == 0x80000000UL || handle == 0x80000001UL);
    ++destroy_count;
}

int main(void)
{
    struct mg_sdk_standard_controls controls;
    mg_sdk_u16 bundle[600];

    assert(mg_sdk_standard_controls_init(&controls, bundle));
    assert(copy_count == 1);
    assert(register_count == 1);
    assert(settings_hides == 1);
    assert(poweroff_hides == 1);
    assert(controls.policy.volume == 4);
    assert(controls.policy.brightness == 1);
    assert(applied_gain == mg_sdk_volume_gain_table[4]);
    assert(applied_backlight == mg_sdk_backlight_table[1]);

    edge_keys = MG_SDK_KEY_VOLUME_UP;
    fake_ticks = 10;
    mg_sdk_standard_controls_poll(&controls);
    assert(saved_volume == 5);
    assert(applied_gain == mg_sdk_volume_gain_table[5]);
    assert(settings_shows == 1);
    assert(controls.last_key == MG_SDK_KEY_VOLUME_UP);
    assert(watchdog_kicks == 1);

    edge_keys = MG_SDK_KEY_BRIGHTNESS;
    fake_ticks = 20;
    mg_sdk_standard_controls_poll(&controls);
    assert(saved_brightness == 2);
    assert(applied_backlight == mg_sdk_backlight_table[2]);
    assert(brightness_shows == 1);
    assert(controls.last_key == MG_SDK_KEY_BRIGHTNESS);
    assert(watchdog_kicks == 2);

    edge_keys = MG_SDK_KEY_OFF;
    fake_ticks = 30;
    mg_sdk_standard_controls_poll(&controls);
    assert(poweroff_shows == 1);
    assert(poweroff_requests == 1);
    assert(controls.last_key == MG_SDK_KEY_OFF);
    assert(watchdog_kicks == 3);

    mg_sdk_standard_controls_hide(&controls);
    assert(settings_hides >= 2);
    assert(poweroff_hides == 2);

    fail_poweroff_create = 1;
    assert(!mg_sdk_standard_controls_init(&controls, bundle));
    assert(destroy_count == 1);
    return 0;
}
