#ifndef MOBIGO_SDK_RESIDENT_KEYS_H
#define MOBIGO_SDK_RESIDENT_KEYS_H

#include "mobigo_sdk/system_controls.h"

/*
 * Direct adapters for the resident key-state services.
 *
 * Call the resident input-update routines from the normal firmware/runtime
 * frame path before querying edges. The application-facing G1 runtime already
 * does this as part of its per-frame input pump.
 */

mg_sdk_u16 mg_sdk_resident_system_keys(void);
int mg_sdk_resident_system_key_down(mg_sdk_u16 mask);
int mg_sdk_resident_system_key_pressed(mg_sdk_u16 mask);
int mg_sdk_resident_system_key_released(mg_sdk_u16 mask);

mg_sdk_u16 mg_sdk_resident_game_keys(void);
int mg_sdk_resident_game_key_down(mg_sdk_u16 mask);
int mg_sdk_resident_game_key_pressed(mg_sdk_u16 mask);
int mg_sdk_resident_game_key_released(mg_sdk_u16 mask);

#endif
