#include "mobigo_sdk/system_controls.h"

const mg_sdk_u16 mg_sdk_volume_gain_table[MG_SDK_VOLUME_LEVELS] = {
    4, 14, 25, 35, 45, 55, 67, 79, 91, 105
};

const mg_sdk_u16 mg_sdk_backlight_table[MG_SDK_BRIGHTNESS_LEVELS] = {
    1, 5, 10, 15
};

static mg_sdk_u32 controls_ticks(
    const struct mg_sdk_system_controls *controls)
{
    if (controls->backend->ticks == 0) {
        return 0;
    }
    return controls->backend->ticks(controls->user);
}

static void controls_show(
    struct mg_sdk_system_controls *controls,
    enum mg_sdk_overlay_kind kind,
    mg_sdk_u16 level,
    mg_sdk_u16 x,
    mg_sdk_u16 y)
{
    if (controls->backend->show_overlay != 0) {
        controls->backend->show_overlay(controls->user, kind, level, x, y);
    }
    controls->overlay_visible = 1;
    controls->overlay_started = controls_ticks(controls);
}

static int controls_key(
    const struct mg_sdk_system_controls *controls,
    mg_sdk_u16 mask)
{
    if (controls->backend->key_pressed_edge == 0) {
        return 0;
    }
    return controls->backend->key_pressed_edge(controls->user, mask) != 0;
}

static void controls_feedback(
    struct mg_sdk_system_controls *controls,
    enum mg_sdk_feedback_kind kind)
{
    if (controls->backend->play_feedback != 0) {
        (void)controls->backend->play_feedback(controls->user, kind);
    }
}

void mg_sdk_system_controls_hide(
    struct mg_sdk_system_controls *controls)
{
    if (controls == 0 || controls->backend == 0) {
        return;
    }
    if (controls->overlay_visible != 0 &&
        controls->backend->hide_overlay != 0) {
        controls->backend->hide_overlay(controls->user);
    }
    controls->overlay_visible = 0;
}

void mg_sdk_volume_set(
    struct mg_sdk_system_controls *controls,
    mg_sdk_u16 level,
    int show_overlay)
{
    if (controls == 0 || controls->backend == 0) {
        return;
    }
    if (level >= MG_SDK_VOLUME_LEVELS) {
        level = MG_SDK_VOLUME_LEVELS - 1;
    }
    controls->volume = level;
    if (controls->backend->apply_master_gain != 0) {
        controls->backend->apply_master_gain(
            controls->user, mg_sdk_volume_gain_table[level]);
    }
    if (controls->backend->save_volume != 0) {
        controls->backend->save_volume(controls->user, level);
    }
    if (show_overlay != 0) {
        controls_show(
            controls,
            MG_SDK_OVERLAY_VOLUME,
            level,
            MG_SDK_VOLUME_OVERLAY_X,
            MG_SDK_SETTING_OVERLAY_Y);
    }
}

void mg_sdk_brightness_set(
    struct mg_sdk_system_controls *controls,
    mg_sdk_u16 level,
    int show_overlay)
{
    if (controls == 0 || controls->backend == 0) {
        return;
    }
    level %= MG_SDK_BRIGHTNESS_LEVELS;
    controls->brightness = level;
    if (controls->backend->apply_backlight != 0) {
        controls->backend->apply_backlight(
            controls->user, mg_sdk_backlight_table[level]);
    }
    if (controls->backend->save_brightness != 0) {
        controls->backend->save_brightness(controls->user, level);
    }
    if (show_overlay != 0) {
        controls_show(
            controls,
            MG_SDK_OVERLAY_BRIGHTNESS,
            level,
            MG_SDK_BRIGHTNESS_OVERLAY_X,
            MG_SDK_SETTING_OVERLAY_Y);
    }
}

void mg_sdk_system_controls_init(
    struct mg_sdk_system_controls *controls,
    const struct mg_sdk_system_backend *backend,
    void *user)
{
    mg_sdk_u16 level;

    if (controls == 0 || backend == 0) {
        return;
    }
    controls->backend = backend;
    controls->user = user;
    controls->overlay_visible = 0;
    controls->poweroff_pending = 0;
    controls->poweroff_sound = -1;
    controls->overlay_started = 0;
    controls->overlay_ticks = MG_SDK_DEFAULT_OVERLAY_TICKS;

    level = MG_SDK_DEFAULT_VOLUME;
    if (backend->load_volume != 0) {
        mg_sdk_u16 saved = level;
        if (backend->load_volume(user, &saved) != 0 &&
            saved < MG_SDK_VOLUME_LEVELS) {
            level = saved;
        }
    }
    controls->volume = level;
    if (backend->apply_master_gain != 0) {
        backend->apply_master_gain(user, mg_sdk_volume_gain_table[level]);
    }

    level = MG_SDK_DEFAULT_BRIGHTNESS;
    if (backend->load_brightness != 0) {
        mg_sdk_u16 saved = level;
        if (backend->load_brightness(user, &saved) != 0 &&
            saved < MG_SDK_BRIGHTNESS_LEVELS) {
            level = saved;
        }
    }
    controls->brightness = level;
    if (backend->apply_backlight != 0) {
        backend->apply_backlight(user, mg_sdk_backlight_table[level]);
    }
}

static void controls_poll_poweroff(
    struct mg_sdk_system_controls *controls)
{
    if (controls->poweroff_pending == 0) {
        if (!controls_key(controls, MG_SDK_KEY_OFF)) {
            return;
        }
        mg_sdk_system_controls_hide(controls);
        controls_show(
            controls,
            MG_SDK_OVERLAY_POWEROFF,
            0,
            MG_SDK_POWEROFF_OVERLAY_X,
            MG_SDK_POWEROFF_OVERLAY_Y);
        controls->poweroff_pending = 1;
        if (controls->backend->play_feedback != 0) {
            controls->poweroff_sound = controls->backend->play_feedback(
                controls->user, MG_SDK_FEEDBACK_POWEROFF);
        }
    }

    if (controls->backend->feedback_active != 0 &&
        controls->poweroff_sound >= 0 &&
        controls->backend->feedback_active(
            controls->user, controls->poweroff_sound) != 0) {
        return;
    }
    if (controls->backend->request_poweroff != 0) {
        controls->backend->request_poweroff(controls->user);
    }
    controls->poweroff_pending = 0;
}

void mg_sdk_system_controls_poll(
    struct mg_sdk_system_controls *controls)
{
    mg_sdk_u32 elapsed;

    if (controls == 0 || controls->backend == 0) {
        return;
    }

    controls_poll_poweroff(controls);
    if (controls->poweroff_pending != 0) {
        return;
    }

    if (controls_key(controls, MG_SDK_KEY_VOLUME_UP)) {
        mg_sdk_u16 level = controls->volume;
        if (level + 1 < MG_SDK_VOLUME_LEVELS) {
            level++;
        }
        controls_feedback(
            controls,
            level == MG_SDK_VOLUME_LEVELS - 1
                ? MG_SDK_FEEDBACK_VOLUME_MAXIMUM
                : MG_SDK_FEEDBACK_SETTING);
        mg_sdk_volume_set(controls, level, 1);
    }
    else if (controls_key(controls, MG_SDK_KEY_VOLUME_DOWN)) {
        mg_sdk_u16 level = controls->volume;
        if (level != 0) {
            level--;
        }
        controls_feedback(controls, MG_SDK_FEEDBACK_SETTING);
        mg_sdk_volume_set(controls, level, 1);
    }

    if (controls_key(controls, MG_SDK_KEY_BRIGHTNESS)) {
        controls_feedback(controls, MG_SDK_FEEDBACK_SETTING);
        mg_sdk_brightness_set(
            controls,
            (mg_sdk_u16)(controls->brightness + 1),
            1);
    }

    if (controls->overlay_visible == 0 ||
        controls->backend->ticks == 0) {
        return;
    }
    elapsed = controls_ticks(controls) - controls->overlay_started;
    if (elapsed >= controls->overlay_ticks) {
        mg_sdk_system_controls_hide(controls);
    }
}
