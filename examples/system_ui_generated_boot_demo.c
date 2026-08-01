#include "mobigo_sdk/resident_runtime.h"
#include "mobigo_clean_system_ui_resources.h"

#define DEMO_BUNDLE_RAM ((unsigned short *)0x5000UL)
#define DEMO_STATUS (*(volatile unsigned short *)0x58f0UL)
#define DEMO_SETTINGS_LOW (*(volatile unsigned short *)0x58f1UL)
#define DEMO_SETTINGS_HIGH (*(volatile unsigned short *)0x58f2UL)
#define DEMO_POWEROFF_LOW (*(volatile unsigned short *)0x58f3UL)
#define DEMO_POWEROFF_HIGH (*(volatile unsigned short *)0x58f4UL)

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
    mg_sdk_u32 scratch;
    mg_sdk_ui_handle settings;
    mg_sdk_ui_handle poweroff;

    DEMO_STATUS = 0x5000;
    scratch = 0;
    if (mg_sdk_resident_runtime_setup(&scratch) == 0) {
        DEMO_STATUS = 0xe401;
        for (;;) {
        }
    }

    mobigo_clean_system_ui_copy_bundle(DEMO_BUNDLE_RAM);
    DEMO_STATUS = 0x5001;
    mobigo_clean_system_ui_register(DEMO_BUNDLE_RAM);
    DEMO_STATUS = 0x5002;

    settings = mobigo_clean_system_ui_create_settings();
    poweroff = mobigo_clean_system_ui_create_poweroff();
    DEMO_SETTINGS_LOW = (unsigned short)settings;
    DEMO_SETTINGS_HIGH = (unsigned short)(settings >> 16);
    DEMO_POWEROFF_LOW = (unsigned short)poweroff;
    DEMO_POWEROFF_HIGH = (unsigned short)(poweroff >> 16);
    if (settings == MG_SDK_INVALID_UI_HANDLE ||
        poweroff == MG_SDK_INVALID_UI_HANDLE) {
        DEMO_STATUS = 0xe402;
        for (;;) {
        }
    }

    /* Render two independent records from the one registered common bundle. */
    mobigo_clean_system_ui_show_brightness(settings, 3);
    mobigo_clean_system_ui_show_poweroff(poweroff);
    DEMO_STATUS = 0x5003;

    callbacks.start = demo_start;
    callbacks.frame = demo_frame;
    callbacks.stop = demo_stop;
    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {
        DEMO_STATUS = 0x5004;
    }

    DEMO_STATUS = 0xe403;
    mg_sdk_resident_runtime_finalize();
    for (;;) {
    }
}
