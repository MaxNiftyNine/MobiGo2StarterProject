#include "mobigo_sdk/resident_runtime.h"
#include "mobigo_clean_system_ui_resources.h"
#include "mobigo_clean_font_resources.h"

#define DEMO_UI_BUNDLE_RAM ((unsigned short *)0x5000UL)
#define DEMO_FONT_BUNDLE_RAM ((unsigned short *)0x5400UL)
#define DEMO_STATUS (*(volatile unsigned short *)0x60f0UL)
#define DEMO_FONT_SLOT (*(volatile unsigned short *)0x60f1UL)
#define DEMO_FIRST_HANDLE_LOW (*(volatile unsigned short *)0x60f2UL)
#define DEMO_FIRST_HANDLE_HIGH (*(volatile unsigned short *)0x60f3UL)
#define DEMO_LAST_HANDLE_LOW (*(volatile unsigned short *)0x60f4UL)
#define DEMO_LAST_HANDLE_HIGH (*(volatile unsigned short *)0x60f5UL)

static const char demo_text[] = "HELLO 123";

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
    mg_sdk_u16 slot;
    mg_sdk_u16 handle_count;
    mg_sdk_ui_handle handles[8];

    DEMO_STATUS = 0x7600;
    DEMO_FONT_SLOT = 0;
    DEMO_FIRST_HANDLE_LOW = 0xffff;
    DEMO_FIRST_HANDLE_HIGH = 0xffff;
    DEMO_LAST_HANDLE_LOW = 0xffff;
    DEMO_LAST_HANDLE_HIGH = 0xffff;

    scratch = 0;
    if (mg_sdk_resident_runtime_setup(&scratch) == 0) {
        DEMO_STATUS = 0xe601;
        for (;;) {
        }
    }

    /* Slot zero establishes the known clean palette used by the font. */
    mobigo_clean_system_ui_copy_bundle(DEMO_UI_BUNDLE_RAM);
    mobigo_clean_system_ui_register(DEMO_UI_BUNDLE_RAM);
    DEMO_STATUS = 0x7601;

    mobigo_clean_font_copy_bundle(DEMO_FONT_BUNDLE_RAM);
    slot = mobigo_clean_font_register_dynamic(DEMO_FONT_BUNDLE_RAM);
    DEMO_FONT_SLOT = slot;
    if (slot == 0) {
        DEMO_STATUS = 0xe602;
        for (;;) {
        }
    }
    DEMO_STATUS = 0x7602;

    handle_count = mobigo_clean_font_create_text(
        slot, demo_text, 92, 108, handles, 8);
    if (handle_count != 8) {
        DEMO_STATUS = 0xe610;
        for (;;) {
        }
    }
    DEMO_FIRST_HANDLE_LOW = (unsigned short)handles[0];
    DEMO_FIRST_HANDLE_HIGH = (unsigned short)(handles[0] >> 16);
    DEMO_LAST_HANDLE_LOW = (unsigned short)handles[handle_count - 1];
    DEMO_LAST_HANDLE_HIGH =
        (unsigned short)(handles[handle_count - 1] >> 16);
    DEMO_STATUS = 0x7603;

    callbacks.start = demo_start;
    callbacks.frame = demo_frame;
    callbacks.stop = demo_stop;
    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {
        DEMO_STATUS = 0x7604;
    }

    DEMO_STATUS = 0xe603;
    mg_sdk_resident_runtime_finalize();
    for (;;) {
    }
}
