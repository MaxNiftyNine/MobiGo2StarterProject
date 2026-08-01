#include "mobigo_sdk/resident_backend.h"
#include "mobigo_sdk/resident_addresses.h"

typedef int (*resident_test_key_fn)(mg_sdk_u16 mask);
typedef mg_sdk_u16 (*resident_get_level_fn)(void);
typedef void (*resident_set_level_fn)(mg_sdk_u16 level);
typedef mg_sdk_u32 (*resident_get_ticks_fn)(void);
typedef void (*resident_poweroff_fn)(void);

#define RESIDENT_SYSTEM_KEY_PRESSED \
    ((resident_test_key_fn)MG_SDK_RESIDENT_SYSTEM_KEY_PRESSED)
#define RESIDENT_APPLY_MASTER_VOLUME \
    ((resident_set_level_fn)MG_SDK_RESIDENT_APPLY_MASTER_VOLUME)
#define RESIDENT_GET_VOLUME \
    ((resident_get_level_fn)MG_SDK_RESIDENT_GET_VOLUME)
#define RESIDENT_SET_VOLUME \
    ((resident_set_level_fn)MG_SDK_RESIDENT_SET_VOLUME)
#define RESIDENT_GET_BRIGHTNESS \
    ((resident_get_level_fn)MG_SDK_RESIDENT_GET_BRIGHTNESS)
#define RESIDENT_SET_BRIGHTNESS \
    ((resident_set_level_fn)MG_SDK_RESIDENT_SET_BRIGHTNESS)
#define RESIDENT_GET_TICKS \
    ((resident_get_ticks_fn)MG_SDK_RESIDENT_GET_TICKS)
#define RESIDENT_APPLY_BACKLIGHT \
    ((resident_set_level_fn)MG_SDK_RESIDENT_APPLY_BACKLIGHT)
#define RESIDENT_REQUEST_POWEROFF \
    ((resident_poweroff_fn)MG_SDK_RESIDENT_REQUEST_POWEROFF)

static int resident_key_pressed_edge(void *user, mg_sdk_u16 mask)
{
    (void)user;
    return RESIDENT_SYSTEM_KEY_PRESSED(mask);
}

static int resident_load_volume(void *user, mg_sdk_u16 *level)
{
    (void)user;
    *level = RESIDENT_GET_VOLUME();
    return 1;
}

static void resident_save_volume(void *user, mg_sdk_u16 level)
{
    (void)user;
    RESIDENT_SET_VOLUME(level);
}

static void resident_apply_master_gain(void *user, mg_sdk_u16 gain)
{
    (void)user;
    RESIDENT_APPLY_MASTER_VOLUME(gain);
}

static int resident_load_brightness(void *user, mg_sdk_u16 *level)
{
    (void)user;
    *level = RESIDENT_GET_BRIGHTNESS();
    return 1;
}

static void resident_save_brightness(void *user, mg_sdk_u16 level)
{
    (void)user;
    RESIDENT_SET_BRIGHTNESS(level);
}

static void resident_apply_backlight(void *user, mg_sdk_u16 value)
{
    (void)user;
    RESIDENT_APPLY_BACKLIGHT(value);
}

static mg_sdk_u32 resident_ticks(void *user)
{
    (void)user;
    return RESIDENT_GET_TICKS();
}

static void resident_request_poweroff(void *user)
{
    (void)user;
    RESIDENT_REQUEST_POWEROFF();
}

const struct mg_sdk_system_backend mg_sdk_experimental_resident_backend = {
    resident_key_pressed_edge,
    resident_load_volume,
    resident_save_volume,
    resident_apply_master_gain,
    resident_load_brightness,
    resident_save_brightness,
    resident_apply_backlight,
    resident_ticks,
    0,
    0,
    0,
    0,
    resident_request_poweroff
};
