#include "mobigo_sdk/direct_controls.h"

#include "mobigo_sdk/resident_backend.h"

static const struct mg_sdk_system_backend *direct_resident(void)
{
    return &mg_sdk_experimental_resident_backend;
}

static int direct_key_pressed_edge(void *user, mg_sdk_u16 mask)
{
    struct mg_sdk_direct_controls *controls =
        (struct mg_sdk_direct_controls *)user;
    return (controls->edge_keys & mask) != 0;
}

static int direct_load_volume(void *user, mg_sdk_u16 *level)
{
    const struct mg_sdk_system_backend *resident = direct_resident();
    (void)user;
    if (resident->load_volume == 0) return 0;
    return resident->load_volume(0, level);
}

static void direct_save_volume(void *user, mg_sdk_u16 level)
{
    const struct mg_sdk_system_backend *resident = direct_resident();
    (void)user;
    if (resident->save_volume != 0) resident->save_volume(0, level);
}

static void direct_apply_master_gain(void *user, mg_sdk_u16 gain)
{
    const struct mg_sdk_system_backend *resident = direct_resident();
    (void)user;
    if (resident->apply_master_gain != 0) {
        resident->apply_master_gain(0, gain);
    }
}

static int direct_load_brightness(void *user, mg_sdk_u16 *level)
{
    const struct mg_sdk_system_backend *resident = direct_resident();
    (void)user;
    if (resident->load_brightness == 0) return 0;
    return resident->load_brightness(0, level);
}

static void direct_save_brightness(void *user, mg_sdk_u16 level)
{
    const struct mg_sdk_system_backend *resident = direct_resident();
    (void)user;
    if (resident->save_brightness != 0) {
        resident->save_brightness(0, level);
    }
}

static void direct_apply_backlight(void *user, mg_sdk_u16 value)
{
    const struct mg_sdk_system_backend *resident = direct_resident();
    (void)user;
    if (resident->apply_backlight != 0) resident->apply_backlight(0, value);
}

static mg_sdk_u32 direct_ticks(void *user)
{
    const struct mg_sdk_system_backend *resident = direct_resident();
    (void)user;
    if (resident->ticks == 0) return 0;
    return resident->ticks(0);
}

static void direct_request_poweroff(void *user)
{
    const struct mg_sdk_system_backend *resident = direct_resident();
    (void)user;
    if (resident->request_poweroff != 0) resident->request_poweroff(0);
}

static const struct mg_sdk_system_backend direct_backend = {
    direct_key_pressed_edge,
    direct_load_volume,
    direct_save_volume,
    direct_apply_master_gain,
    direct_load_brightness,
    direct_save_brightness,
    direct_apply_backlight,
    direct_ticks,
    0,
    0,
    0,
    0,
    direct_request_poweroff
};

int mg_sdk_direct_controls_init(struct mg_sdk_direct_controls *controls)
{
    if (controls == 0) {
        return 0;
    }
    controls->initialized = 0;
    controls->previous_keys = 0;
    controls->edge_keys = 0;
    mg_sdk_matrix_init();
    mg_sdk_matrix_scan(&controls->matrix);
    controls->previous_keys = mg_sdk_matrix_system_keys(&controls->matrix);
    mg_sdk_system_controls_init(&controls->policy, &direct_backend, controls);
    controls->initialized = 1;
    return 1;
}

void mg_sdk_direct_controls_poll(struct mg_sdk_direct_controls *controls)
{
    mg_sdk_u16 keys;
    if (controls == 0 || controls->initialized == 0) {
        return;
    }
    mg_sdk_matrix_scan(&controls->matrix);
    keys = mg_sdk_matrix_system_keys(&controls->matrix);
    controls->edge_keys =
        (mg_sdk_u16)(keys & (mg_sdk_u16)~controls->previous_keys);
    controls->previous_keys = keys;
    mg_sdk_system_controls_poll(&controls->policy);
    controls->edge_keys = 0;
    mg_sdk_watchdog_kick();
}

void mg_sdk_direct_controls_hide(struct mg_sdk_direct_controls *controls)
{
    if (controls == 0 || controls->initialized == 0) {
        return;
    }
    mg_sdk_system_controls_hide(&controls->policy);
}
