#ifndef MOBIGO_SDK_APPLICATION_H
#define MOBIGO_SDK_APPLICATION_H

#include "mobigo_sdk/system_controls.h"

/*
 * Target-only application handoff API.
 *
 * Paths use the MobiGo volume form, for example:
 *     A:\BUNDLE\SY\135800SY.MBA
 *
 * The resident launcher copies at most 42 path bytes and at most sixteen
 * 32-bit argument values before scheduling the handoff. This call does not
 * jump immediately. After calling it from a runtime frame callback, return
 * zero from that callback so runtime_step can stop and runtime_finalize can
 * complete the resident handoff, then return from the MBA entry. Official G1
 * and SY transitions normally pass one 32-bit argument with value 999.
 */
enum {
    MG_SDK_LAUNCH_PATH_BYTES = 42,
    MG_SDK_LAUNCH_MAX_ARGUMENTS = 16
};

int mg_sdk_resident_path_exists(const char *path);

void mg_sdk_resident_launch_mba(
    const char *path,
    mg_sdk_u16 argument_count,
    const mg_sdk_u32 *arguments);

#endif
