#include "mobigo_sdk/mobigo_sdk.h"

static int app_start(void)
{
    /* Load original homebrew resources and initialize game state here. */
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    (void)ticks;
    /*
     * Resident key edges and touch records have already been updated for
     * this frame. Return zero when the application should stop.
     */
    return 1;
}

static void app_stop(void)
{
    /* Release application-owned resources here. */
}

static const struct mg_sdk_runtime_callbacks app_callbacks = {
    app_start,
    app_frame,
    app_stop
};

int example_run_resident_lifecycle(void)
{
    return mg_sdk_resident_run(&app_callbacks);
}
