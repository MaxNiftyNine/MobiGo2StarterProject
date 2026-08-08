#ifndef MOBIGO_SDK_DIRECT_CONTROLS_H
#define MOBIGO_SDK_DIRECT_CONTROLS_H

#include "mobigo_sdk/hardware.h"

/*
 * Target-only controls for direct framebuffer loops which do not step the
 * resident application lifecycle.  Matrix edges are handled locally while
 * persistent levels, hardware application, and power-off still use the
 * resident services.  No overlay is drawn because resident UI rendering is
 * not active in this profile.
 */
struct mg_sdk_direct_controls {
    struct mg_sdk_system_controls policy;
    struct mg_sdk_matrix_state matrix;
    mg_sdk_u16 previous_keys;
    mg_sdk_u16 edge_keys;
    mg_sdk_u16 initialized;
};

int mg_sdk_direct_controls_init(struct mg_sdk_direct_controls *controls);
void mg_sdk_direct_controls_poll(struct mg_sdk_direct_controls *controls);
void mg_sdk_direct_controls_hide(struct mg_sdk_direct_controls *controls);

#endif
