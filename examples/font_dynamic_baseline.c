#include "mobigo_sdk/resident_runtime.h"
#include "mobigo_clean_system_ui_resources.h"
#include "mobigo_clean_font_resources.h"

#define DEMO_UI_BUNDLE_RAM ((unsigned short *)0x5000UL)
#define DEMO_FONT_BUNDLE_RAM ((unsigned short *)0x5400UL)
#define DEMO_STATUS (*(volatile unsigned short *)0x60f0UL)
#define DEMO_FONT_SLOT (*(volatile unsigned short *)0x60f1UL)

static int demo_start(void) { return 1; }
static int demo_frame(mg_sdk_u32 ticks) { (void)ticks; return 1; }
static void demo_stop(void) {}

int main(void)
{
    struct mg_sdk_runtime_callbacks callbacks;
    mg_sdk_u32 scratch;
    mg_sdk_u16 slot;

    DEMO_STATUS = 0x7610;
    scratch = 0;
    if (mg_sdk_resident_runtime_setup(&scratch) == 0) {
        DEMO_STATUS = 0xe621;
        for (;;) {}
    }
    mobigo_clean_system_ui_copy_bundle(DEMO_UI_BUNDLE_RAM);
    mobigo_clean_system_ui_register(DEMO_UI_BUNDLE_RAM);
    mobigo_clean_font_copy_bundle(DEMO_FONT_BUNDLE_RAM);
    slot = mobigo_clean_font_register_dynamic(DEMO_FONT_BUNDLE_RAM);
    DEMO_FONT_SLOT = slot;
    if (slot == 0) {
        DEMO_STATUS = 0xe622;
        for (;;) {}
    }
    DEMO_STATUS = 0x7611;
    callbacks.start = demo_start;
    callbacks.frame = demo_frame;
    callbacks.stop = demo_stop;
    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {
        DEMO_STATUS = 0x7612;
    }
    for (;;) {}
}
