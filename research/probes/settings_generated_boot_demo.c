#include "mobigo_sdk/resident_runtime.h"
#include "mobigo_sdk/settings_overlay.h"
#include "mobigo_clean_settings_resources.h"

#define DEMO_BUNDLE_RAM ((unsigned short *)0x5000UL)
#define DEMO_STATUS (*(volatile unsigned short *)0x58f0UL)
#define DEMO_HANDLE_LOW (*(volatile unsigned short *)0x58f1UL)
#define DEMO_HANDLE_HIGH (*(volatile unsigned short *)0x58f2UL)

static int demo_start(void)
{
    return 1;
}

static int demo_frame(mg_sdk_u32 ticks)
{
    (void)ticks;
    return 1;
}

static void demo_stop(void)
{
}

int main(void)
{
    struct mg_sdk_runtime_callbacks callbacks;
    struct mg_sdk_settings_object *object;
    mg_sdk_u32 scratch;
    mg_sdk_ui_handle handle;

    DEMO_STATUS = 0x3000;
    scratch = 0;
    if (mg_sdk_resident_runtime_setup(&scratch) == 0) {
        DEMO_STATUS = 0xe201;
        for (;;) {
        }
    }

    mobigo_clean_settings_copy_bundle(DEMO_BUNDLE_RAM);
    DEMO_STATUS = 0x3001;
    mobigo_clean_settings_register(DEMO_BUNDLE_RAM);
    DEMO_STATUS = 0x3002;

    handle = mobigo_clean_settings_create();
    DEMO_HANDLE_LOW = (unsigned short)handle;
    DEMO_HANDLE_HIGH = (unsigned short)(handle >> 16);
    if (handle == MG_SDK_INVALID_UI_HANDLE) {
        DEMO_STATUS = 0xe202;
        for (;;) {
        }
    }

    object = (struct mg_sdk_settings_object *)mg_sdk_ui_b_get(handle);
    if (object == (struct mg_sdk_settings_object *)0) {
        DEMO_STATUS = 0xe203;
        for (;;) {
        }
    }
    mg_sdk_settings_object_prepare(object, 0x6d, 0xd6);
#ifdef DEMO_VOLUME
    mg_sdk_settings_object_show(
        object,
        MOBIGO_CLEAN_SETTINGS_VOLUME_MODE,
        9,
        0x8a,
        0xd6);
#else
    mg_sdk_settings_object_show(
        object,
        MOBIGO_CLEAN_SETTINGS_BRIGHTNESS_MODE,
        3,
        0x6d,
        0xd6);
#endif
    DEMO_STATUS = 0x3003;

    callbacks.start = demo_start;
    callbacks.frame = demo_frame;
    callbacks.stop = demo_stop;
    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {
        DEMO_STATUS = 0x3004;
    }

    DEMO_STATUS = 0xe204;
    mg_sdk_resident_runtime_finalize();
    for (;;) {
    }
}
