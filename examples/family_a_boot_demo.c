#include "mobigo_sdk/resident_runtime.h"
#include "mobigo_sdk/resident_resources.h"

/*
 * Boot-time validation for the clean-room family-A grammar.
 *
 * No initialized globals are used: the MobiGo MBA handoff enters main()
 * directly, without a C runtime data-copy pass.  The bundle and primary image
 * are constructed into BSS storage before registration.
 */

enum {
    DEMO_BUNDLE_WORDS = 64,
    DEMO_PRIMARY_WORDS = 0x840,
    DEMO_PALETTE1 = 0x200,
    DEMO_TILEMAP = 0x400,
    DEMO_GRAPHICS = 0x800,
    DEMO_TILE_WORDS = 0x20
};

/*
 * The resident firmware owns low IRAM (including state around 0x0aa0 and
 * larger graphics/work tables around 0x3000).  The retail applications place
 * their writable title state in the 0x5000 range.  Use that application arena
 * explicitly instead of allowing -mglobal-var-iram to allocate a large BSS
 * object from address zero.
 */
#define demo_bundle ((mg_sdk_u16 *)0x5000UL)
#define demo_primary ((mg_sdk_u16 *)0x5040UL)
#define demo_status (*(volatile mg_sdk_u16 *)0x58f0UL)
#define demo_handle_low (*(volatile mg_sdk_u16 *)0x58f1UL)
#define demo_handle_high (*(volatile mg_sdk_u16 *)0x58f2UL)

static void put_u32(mg_sdk_u16 *words, mg_sdk_u16 offset, mg_sdk_u32 value)
{
    words[offset] = (mg_sdk_u16)value;
    words[offset + 1] = (mg_sdk_u16)(value >> 16);
}

static void build_demo_resources(void)
{
    mg_sdk_u16 index;

    for (index = 0; index < DEMO_BUNDLE_WORDS; ++index) {
        demo_bundle[index] = 0;
    }
    for (index = 0; index < DEMO_PRIMARY_WORDS; ++index) {
        demo_primary[index] = 0;
    }

    /* Version-2 bundle header. Relative pointers use header+0x20 as base. */
    put_u32(demo_bundle, 0x00, 0x80000002UL);
    put_u32(demo_bundle, 0x02, 0x80000000UL);
    put_u32(demo_bundle, 0x04, 0x80000200UL);
    put_u32(demo_bundle, 0x06, 0xc0000000UL);
    put_u32(demo_bundle, 0x08, 0xc0000100UL);
    demo_bundle[0x0a] = 0;             /* lookup count */
    put_u32(demo_bundle, 0x0c, 0);    /* empty lookup / A table */
    put_u32(demo_bundle, 0x10, 0);    /* auxiliary / A table */
    demo_bundle[0x12] = 1;            /* family-A descriptor count */
    put_u32(demo_bundle, 0x14, 0);    /* family-A table starts at word 0x20 */
    demo_bundle[0x16] = 0;            /* no family-B descriptors */
    put_u32(demo_bundle, 0x18, 10);   /* family-B empty marker */
    put_u32(demo_bundle, 0x1a, 10);   /* generated handle storage */

    /* 10-word family-A descriptor at bundle word 0x20. */
    demo_bundle[0x20] = 1;
    demo_bundle[0x25] = 0x40;
    demo_bundle[0x26] = 0xffff;
    demo_bundle[0x27] = 0xffff;
    put_u32(demo_bundle, 0x28, 12);   /* -> image record at word 0x2c */

    /* 18-word family-A image record at bundle word 0x2c. */
    demo_bundle[0x2c + 0] = 320;
    demo_bundle[0x2c + 1] = 240;
    demo_bundle[0x2c + 2] = 16;
    demo_bundle[0x2c + 3] = 16;
    demo_bundle[0x2c + 4] = 0;        /* resident format 0 = 2-bpp tiled */
    demo_bundle[0x2c + 5] = 0;
    demo_bundle[0x2c + 6] = 239;
    demo_bundle[0x2c + 7] = 0;
    demo_bundle[0x2c + 8] = 319;
    demo_bundle[0x2c + 9] = 0;
    put_u32(demo_bundle, 0x2c + 10, 0x80000800UL); /* graphics */
    put_u32(demo_bundle, 0x2c + 12, 0x80000400UL); /* tilemap source */
    demo_bundle[0x2c + 14] = 0;       /* palette selector */
    demo_bundle[0x2c + 15] = 0;
    put_u32(demo_bundle, 0x2c + 16, 30); /* -> runtime slot at word 0x3e */

    /* Palette source zero. Index zero stays black; 1/2 make visible stripes. */
    demo_primary[0] = 0x0000;
    demo_primary[1] = 0x7c00; /* red */
    demo_primary[2] = 0x03e0; /* green */
    demo_primary[3] = 0x001f; /* blue */

    /* Every visible page cell uses tile #1. */
    for (index = DEMO_TILEMAP; index < DEMO_GRAPHICS; ++index) {
        demo_primary[index] = 1;
    }

    /* Tile zero is blank. Tile one alternates red/green rows. */
    for (index = 0; index < DEMO_TILE_WORDS; ++index) {
        demo_primary[DEMO_GRAPHICS + index] = 0;
        demo_primary[DEMO_GRAPHICS + DEMO_TILE_WORDS + index] =
            ((index >> 1) & 1) ? 0xaaaa : 0x5555;
    }
}

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

    demo_status = 0x1000;
    build_demo_resources();
    demo_status = 0x1001;

    scratch = 0;
    if (mg_sdk_resident_runtime_setup(&scratch) == 0) {
        demo_status = 0xe001;
        for (;;) {
        }
    }
    demo_status = 0x1002;

    mg_sdk_resident_register_asset_bundle(demo_bundle, demo_primary, (void *)0);
    demo_status = 0x1003;

    handle = mg_sdk_ui_a_create(0);
    demo_handle_low = (mg_sdk_u16)handle;
    demo_handle_high = (mg_sdk_u16)(handle >> 16);
    if (handle == MG_SDK_INVALID_UI_HANDLE) {
        demo_status = 0xe002;
        for (;;) {
        }
    }
    demo_status = 0x1004;

    callbacks.start = demo_start;
    callbacks.frame = demo_frame;
    callbacks.stop = demo_stop;

    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {
        demo_status = 0x1005;
    }

    demo_status = 0xe003;
    mg_sdk_resident_runtime_finalize();
    for (;;) {
    }
}
