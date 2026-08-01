#include "mobigo_sdk/resident_runtime.h"
#include "mobigo_clean_family_a_resources.h"

/*
 * End-to-end validation of generated family-A resources. The linked resource
 * payload is const executable data. Only the small bundle graph is copied to
 * writable application RAM because the resident registrar rebases it in place.
 */
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
    mg_sdk_u32 scratch;
    mg_sdk_ui_handle handle;

    DEMO_STATUS = 0x2000;
    scratch = 0;
    if (mg_sdk_resident_runtime_setup(&scratch) == 0) {
        DEMO_STATUS = 0xe101;
        for (;;) {
        }
    }

    mobigo_clean_family_a_copy_bundle(DEMO_BUNDLE_RAM);
    /*
     * Header word 0x1a points at the registrar auto-instance table. For this
     * one-descriptor bundle the marker occupies words 42..43 and the parallel
     * output handle occupies words 44..45. TM uses the same nonzero marker
     * convention for its family-A descriptor zero.
     */
    DEMO_BUNDLE_RAM[42] = 1;
    DEMO_BUNDLE_RAM[43] = 0;
    DEMO_STATUS = 0x2001;
    mobigo_clean_family_a_register(DEMO_BUNDLE_RAM);
    DEMO_STATUS = 0x2002;

    handle = (mg_sdk_ui_handle)DEMO_BUNDLE_RAM[44]
        | ((mg_sdk_ui_handle)DEMO_BUNDLE_RAM[45] << 16);
    DEMO_HANDLE_LOW = (unsigned short)handle;
    DEMO_HANDLE_HIGH = (unsigned short)(handle >> 16);
    if (handle == 0 || handle == MG_SDK_INVALID_UI_HANDLE) {
        DEMO_STATUS = 0xe102;
        for (;;) {
        }
    }
    DEMO_STATUS = 0x2003;

    callbacks.start = demo_start;
    callbacks.frame = demo_frame;
    callbacks.stop = demo_stop;
    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {
        DEMO_STATUS = 0x2004;
    }

    DEMO_STATUS = 0xe103;
    mg_sdk_resident_runtime_finalize();
    for (;;) {
    }
}
