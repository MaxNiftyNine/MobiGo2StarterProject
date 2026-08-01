#ifndef MOBIGO_SDK_RESIDENT_RUNTIME_H
#define MOBIGO_SDK_RESIDENT_RUNTIME_H

#include "mobigo_sdk/system_controls.h"

typedef int (*mg_sdk_runtime_start_fn)(void);
typedef int (*mg_sdk_runtime_frame_fn)(mg_sdk_u32 ticks);
typedef void (*mg_sdk_runtime_stop_fn)(void);

/*
 * Exact target layout: three 32-bit far function pointers, six 16-bit words.
 * The Generalplus u'nSP compiler used by this project has 32-bit pointers.
 */
struct mg_sdk_runtime_callbacks {
    mg_sdk_runtime_start_fn start;
    mg_sdk_runtime_frame_fn frame;
    mg_sdk_runtime_stop_fn stop;
};

/*
 * setup accepts the same reserved two-word scratch pointer passed by G1.
 * The captured firmware currently ignores its contents.
 */
int mg_sdk_resident_runtime_setup(mg_sdk_u32 *reserved_scratch);
int mg_sdk_resident_runtime_step(
    const struct mg_sdk_runtime_callbacks *callbacks);
void mg_sdk_resident_runtime_finalize(void);

/*
 * Run the standard resident lifecycle until either start/frame returns zero.
 * Returns zero when setup fails, otherwise one after orderly finalization.
 */
int mg_sdk_resident_run(
    const struct mg_sdk_runtime_callbacks *callbacks);

#endif
