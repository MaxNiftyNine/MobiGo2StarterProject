#include "mobigo_sdk/mobigo_sdk.h"

#define OUT ((volatile mg_sdk_u16 *)0x59c0UL)

static const char *const paths[] = {
    "A:",
    "A:\\",
    "A:BUNDLE",
    "A:\\BUNDLE",
    "A:BUNDLE\\SY",
    "A:\\BUNDLE\\SY",
    "A:BUNDLE\\SY\\135804SY.MBA",
    "A:\\BUNDLE\\SY\\135804SY.MBA",
    "A:DEGER",
    "A:\\DEGER",
    "A:DEGER\\MBASORT.LST",
    "A:\\DEGER\\MBASORT.LST",
    "A:ETC\\PROFILE.DAT",
    "A:\\ETC\\PROFILE.DAT"
};

static int app_start(void)
{
    mg_sdk_u16 i;
    for (i = 0; i < (mg_sdk_u16)(sizeof(paths) / sizeof(paths[0])); ++i) {
        OUT[i] = (mg_sdk_u16)mg_sdk_resident_storage_path_exists(paths[i]);
    }
    OUT[15] = 0x7301;
    return 1;
}
static int app_frame(mg_sdk_u32 ticks) { (void)ticks; return 1; }
static void app_stop(void) {}
static const struct mg_sdk_runtime_callbacks callbacks = { app_start, app_frame, app_stop };
int main(void) { mg_sdk_resident_run(&callbacks); for (;;) {} }
