#include "mobigo_sdk/mobigo_sdk.h"

/*
 * Minimal resident-lifecycle starter.
 *
 * A direct MBA entry does not run a conventional initialized-data CRT.  The
 * maintained template therefore keeps its generated bundle and controller in
 * the documented title-RAM reservations and initializes both explicitly.
 */
#define APP_BUNDLE_RAM \
    ((mg_sdk_u16 *)MG_SDK_DEFAULT_SYSTEM_UI_WORD_ADDRESS)
#define APP_CONTROLS \
    ((struct mg_sdk_standard_controls *) \
        MG_SDK_DEFAULT_STANDARD_CONTROLS_WORD_ADDRESS)

static int app_start(void)
{
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    (void)ticks;
    mg_sdk_standard_controls_poll(APP_CONTROLS);
    return 1;
}

static void app_stop(void)
{
    mg_sdk_standard_controls_hide(APP_CONTROLS);
}

int main(void)
{
    struct mg_sdk_runtime_callbacks callbacks;
    mg_sdk_u32 scratch = 0;

    if (mg_sdk_resident_runtime_setup(&scratch) == 0) {
        return 0;
    }
    if (mg_sdk_standard_controls_init(APP_CONTROLS, APP_BUNDLE_RAM) == 0) {
        mg_sdk_resident_runtime_finalize();
        return 0;
    }

    callbacks.start = app_start;
    callbacks.frame = app_frame;
    callbacks.stop = app_stop;
    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {
    }

    mg_sdk_standard_controls_hide(APP_CONTROLS);
    mg_sdk_resident_runtime_finalize();
    return 0;
}
