#ifndef MOBIGO_SDK_STANDARD_CONTROLS_H
#define MOBIGO_SDK_STANDARD_CONTROLS_H

#include "mobigo_sdk/resident_resources.h"
#include "mobigo_sdk/system_controls.h"

/*
 * Target-only standard volume, brightness, and Off controller.
 *
 * The default SDK build links the generated clean system-UI resource adapter
 * required by this API.  The caller supplies writable title RAM for that
 * bundle; registration relocates it in place.  Poll once per resident-runtime
 * frame after the firmware has updated key edges.
 */
struct mg_sdk_standard_controls {
    struct mg_sdk_system_controls policy;
    mg_sdk_ui_handle settings_handle;
    mg_sdk_ui_handle poweroff_handle;
    mg_sdk_u16 initialized;
    mg_sdk_u16 last_key;
};

int mg_sdk_standard_controls_init(
    struct mg_sdk_standard_controls *controls,
    mg_sdk_u16 *bundle_ram);

void mg_sdk_standard_controls_poll(
    struct mg_sdk_standard_controls *controls);

void mg_sdk_standard_controls_hide(
    struct mg_sdk_standard_controls *controls);

#endif
