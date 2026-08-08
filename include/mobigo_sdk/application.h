#ifndef MOBIGO_SDK_APPLICATION_H
#define MOBIGO_SDK_APPLICATION_H

#include "mobigo_sdk/system_controls.h"

/*
 * Target-only application handoff API.
 *
 * Paths use the packed MobiGo volume form:
 *     <volume>:\BUNDLE\<role>\<title>.MBA
 *
 * The resident launcher copies at most 42 path bytes (41 characters plus the
 * required terminator) and at most sixteen 32-bit argument values before
 * scheduling the handoff. This call does not
 * jump immediately. After calling it from a runtime frame callback, return
 * zero from that callback so runtime_step can stop and runtime_finalize can
 * complete the resident handoff, then return from the MBA entry. The bundled
 * verified firmware fixture uses one 32-bit argument with value 999 for its
 * observed G1/SY transitions; that value is evidence for those call sites,
 * not a universal application argument contract.
 */
enum {
    MG_SDK_LAUNCH_PATH_WORDS = 21,
    MG_SDK_LAUNCH_PATH_BYTES = 42,
    MG_SDK_LAUNCH_PATH_MAX_CHARS = 41,
    MG_SDK_LAUNCH_MAX_ARGUMENTS = 16
};

/* Pack a launch path independently of the resident filesystem wrappers'
 * shorter normalization buffer.  Returns zero rather than truncating when a
 * NUL-terminated path exceeds MAX_CHARS. */
int mg_sdk_launch_pack_path(
    mg_sdk_u16 *destination,
    const char *source);

int mg_sdk_resident_path_exists(const char *path);

void mg_sdk_resident_launch_mba(
    const char *path,
    mg_sdk_u16 argument_count,
    const mg_sdk_u32 *arguments);

#endif
