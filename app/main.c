#include "mobigo_sdk/mobigo_sdk.h"
#include "mobigo_clean_system_ui_resources.h"

/*
 * Clean-room homebrew starter using the recovered official-style lifecycle.
 *
 * IMPORTANT: a raw MBA handoff enters main() without a normal initialized-data
 * CRT pass. Keep mutable state in explicitly chosen title RAM or initialize it
 * yourself before use. This template uses the emulator-proven title arena at
 * 0x5000..0x58ff. Hardware validation of this exact allocation is still pending.
 */
#define APP_BUNDLE_RAM ((unsigned short *)0x5000UL)
#define APP_STATE ((volatile unsigned short *)0x58c0UL)

enum {
    APP_STATE_STATUS = 0,
    APP_STATE_SETTINGS_LO = 1,
    APP_STATE_SETTINGS_HI = 2,
    APP_STATE_POWEROFF_LO = 3,
    APP_STATE_POWEROFF_HI = 4,
    APP_STATE_VOLUME = 5,
    APP_STATE_BRIGHTNESS = 6,
    APP_STATE_LAST_KEY = 7
};

static mg_sdk_ui_handle load_handle(unsigned short low_word)
{
    return (mg_sdk_ui_handle)APP_STATE[low_word]
        | ((mg_sdk_ui_handle)APP_STATE[low_word + 1] << 16);
}

static void store_handle(unsigned short low_word, mg_sdk_ui_handle handle)
{
    APP_STATE[low_word] = (unsigned short)handle;
    APP_STATE[low_word + 1] = (unsigned short)(handle >> 16);
}

static int app_start(void)
{
    APP_STATE[APP_STATE_STATUS] = 0x6003;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    mg_sdk_ui_handle settings = load_handle(APP_STATE_SETTINGS_LO);
    mg_sdk_ui_handle poweroff = load_handle(APP_STATE_POWEROFF_LO);
    unsigned short level;
    (void)ticks;

    if (mg_sdk_resident_system_key_pressed(MG_SDK_KEY_VOLUME_UP)) {
        level = APP_STATE[APP_STATE_VOLUME];
        if (level + 1 < MG_SDK_VOLUME_LEVELS) {
            ++level;
        }
        APP_STATE[APP_STATE_VOLUME] = level;
        APP_STATE[APP_STATE_LAST_KEY] = MG_SDK_KEY_VOLUME_UP;
        mobigo_clean_system_ui_show_volume(settings, level);
    }

    if (mg_sdk_resident_system_key_pressed(MG_SDK_KEY_VOLUME_DOWN)) {
        level = APP_STATE[APP_STATE_VOLUME];
        if (level != 0) {
            --level;
        }
        APP_STATE[APP_STATE_VOLUME] = level;
        APP_STATE[APP_STATE_LAST_KEY] = MG_SDK_KEY_VOLUME_DOWN;
        mobigo_clean_system_ui_show_volume(settings, level);
    }

    if (mg_sdk_resident_system_key_pressed(MG_SDK_KEY_BRIGHTNESS)) {
        level = APP_STATE[APP_STATE_BRIGHTNESS] + 1;
        if (level >= MG_SDK_BRIGHTNESS_LEVELS) {
            level = 0;
        }
        APP_STATE[APP_STATE_BRIGHTNESS] = level;
        APP_STATE[APP_STATE_LAST_KEY] = MG_SDK_KEY_BRIGHTNESS;
        mobigo_clean_system_ui_show_brightness(settings, level);
    }

    if (mg_sdk_resident_system_key_pressed(MG_SDK_KEY_OFF)) {
        APP_STATE[APP_STATE_LAST_KEY] = MG_SDK_KEY_OFF;
        mobigo_clean_system_ui_show_poweroff(poweroff);
    }

    APP_STATE[APP_STATE_STATUS] = 0x6004;
    return 1;
}

static void app_stop(void)
{
    APP_STATE[APP_STATE_STATUS] = 0x6005;
}

int main(void)
{
    struct mg_sdk_runtime_callbacks callbacks;
    mg_sdk_ui_handle settings;
    mg_sdk_ui_handle poweroff;
    mg_sdk_u32 scratch = 0;

    APP_STATE[APP_STATE_STATUS] = 0x6000;
    APP_STATE[APP_STATE_VOLUME] = MG_SDK_DEFAULT_VOLUME;
    APP_STATE[APP_STATE_BRIGHTNESS] = MG_SDK_DEFAULT_BRIGHTNESS;
    APP_STATE[APP_STATE_LAST_KEY] = 0;

    if (mg_sdk_resident_runtime_setup(&scratch) == 0) {
        APP_STATE[APP_STATE_STATUS] = 0xe501;
        for (;;) {
        }
    }

    mobigo_clean_system_ui_copy_bundle(APP_BUNDLE_RAM);
    mobigo_clean_system_ui_register(APP_BUNDLE_RAM);
    APP_STATE[APP_STATE_STATUS] = 0x6001;

    settings = mobigo_clean_system_ui_create_settings();
    poweroff = mobigo_clean_system_ui_create_poweroff();
    store_handle(APP_STATE_SETTINGS_LO, settings);
    store_handle(APP_STATE_POWEROFF_LO, poweroff);
    if (settings == MG_SDK_INVALID_UI_HANDLE ||
        poweroff == MG_SDK_INVALID_UI_HANDLE) {
        APP_STATE[APP_STATE_STATUS] = 0xe502;
        for (;;) {
        }
    }
    APP_STATE[APP_STATE_STATUS] = 0x6002;

    callbacks.start = app_start;
    callbacks.frame = app_frame;
    callbacks.stop = app_stop;

    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {
    }

    mg_sdk_resident_runtime_finalize();
    APP_STATE[APP_STATE_STATUS] = 0xe503;
    for (;;) {
    }
}
