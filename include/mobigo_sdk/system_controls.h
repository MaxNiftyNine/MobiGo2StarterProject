#ifndef MOBIGO_SDK_SYSTEM_CONTROLS_H
#define MOBIGO_SDK_SYSTEM_CONTROLS_H

/*
 * Clean-room MobiGo system-controls policy.
 *
 * This interface recreates observed behavior without embedding retail code,
 * artwork, or sounds. A platform adapter supplies input, persistence, hardware
 * setting, presentation, and power operations.
 */

typedef unsigned short mg_sdk_u16;
typedef signed short mg_sdk_s16;
#if defined(__LP64__) || defined(_WIN64)
typedef unsigned int mg_sdk_u32;
#else
typedef unsigned long mg_sdk_u32;
#endif

enum mg_sdk_system_key {
    MG_SDK_KEY_OFF = 0x0200,
    MG_SDK_KEY_VOLUME_UP = 0x0400,
    MG_SDK_KEY_VOLUME_DOWN = 0x0800,
    MG_SDK_KEY_BRIGHTNESS = 0x1000
};

enum mg_sdk_overlay_kind {
    MG_SDK_OVERLAY_NONE = 0,
    MG_SDK_OVERLAY_BRIGHTNESS = 1,
    MG_SDK_OVERLAY_VOLUME = 2,
    MG_SDK_OVERLAY_POWEROFF = 3
};

enum mg_sdk_feedback_kind {
    MG_SDK_FEEDBACK_SETTING = 1,
    MG_SDK_FEEDBACK_VOLUME_MAXIMUM = 2,
    MG_SDK_FEEDBACK_POWEROFF = 3
};

enum {
    MG_SDK_VOLUME_LEVELS = 10,
    MG_SDK_BRIGHTNESS_LEVELS = 4,
    MG_SDK_DEFAULT_VOLUME = 7,
    MG_SDK_DEFAULT_BRIGHTNESS = 2,
    MG_SDK_VOLUME_OVERLAY_X = 109,
    MG_SDK_BRIGHTNESS_OVERLAY_X = 138,
    MG_SDK_SETTING_OVERLAY_Y = 214,
    MG_SDK_POWEROFF_OVERLAY_X = 160,
    MG_SDK_POWEROFF_OVERLAY_Y = 120
};

#define MG_SDK_DEFAULT_OVERLAY_TICKS ((mg_sdk_u32)0x13f1UL)

extern const mg_sdk_u16
    mg_sdk_volume_gain_table[MG_SDK_VOLUME_LEVELS];
extern const mg_sdk_u16
    mg_sdk_backlight_table[MG_SDK_BRIGHTNESS_LEVELS];

struct mg_sdk_system_backend {
    int (*key_pressed_edge)(void *user, mg_sdk_u16 key_mask);
    int (*load_volume)(void *user, mg_sdk_u16 *level);
    void (*save_volume)(void *user, mg_sdk_u16 level);
    void (*apply_master_gain)(void *user, mg_sdk_u16 gain);
    int (*load_brightness)(void *user, mg_sdk_u16 *level);
    void (*save_brightness)(void *user, mg_sdk_u16 level);
    void (*apply_backlight)(void *user, mg_sdk_u16 value);
    mg_sdk_u32 (*ticks)(void *user);
    void (*show_overlay)(
        void *user,
        enum mg_sdk_overlay_kind kind,
        mg_sdk_u16 level,
        mg_sdk_u16 x,
        mg_sdk_u16 y);
    void (*hide_overlay)(void *user);
    int (*play_feedback)(void *user, enum mg_sdk_feedback_kind kind);
    int (*feedback_active)(void *user, int handle);
    void (*request_poweroff)(void *user);
};

struct mg_sdk_system_controls {
    const struct mg_sdk_system_backend *backend;
    void *user;
    mg_sdk_u16 volume;
    mg_sdk_u16 brightness;
    mg_sdk_u16 overlay_visible;
    mg_sdk_u16 poweroff_pending;
    int poweroff_sound;
    mg_sdk_u32 overlay_started;
    mg_sdk_u32 overlay_ticks;
};

void mg_sdk_system_controls_init(
    struct mg_sdk_system_controls *controls,
    const struct mg_sdk_system_backend *backend,
    void *user);

void mg_sdk_system_controls_poll(
    struct mg_sdk_system_controls *controls);

void mg_sdk_system_controls_hide(
    struct mg_sdk_system_controls *controls);

void mg_sdk_volume_set(
    struct mg_sdk_system_controls *controls,
    mg_sdk_u16 level,
    int show_overlay);

void mg_sdk_brightness_set(
    struct mg_sdk_system_controls *controls,
    mg_sdk_u16 level,
    int show_overlay);

#endif
