#include "mobigo_sdk/mobigo_sdk.h"

#define OUT ((volatile mg_sdk_u16 *)0x59e0UL)

typedef int (*resident_path_remove_fn)(const mg_sdk_u16 *packed_path);
#define RESIDENT_PATH_REMOVE \
    ((resident_path_remove_fn)MG_SDK_RESIDENT_PATH_REMOVE)

static const char test_path[] = "A:DEGER\\MBASORT.LST";

static int app_start(void)
{
    mg_sdk_u16 packed[MG_SDK_STORAGE_PATH_WORDS];
    OUT[0] = (mg_sdk_u16)mg_sdk_resident_storage_path_exists(test_path);
    OUT[1] = 0xffff;
    OUT[2] = 0xffff;
    OUT[3] = 0x7400;
    if (OUT[0] != 1 || !mg_sdk_storage_pack_path(packed, test_path)) {
        OUT[3] = 0xe740;
        return 1;
    }
    OUT[1] = (mg_sdk_u16)RESIDENT_PATH_REMOVE(packed);
    OUT[2] = (mg_sdk_u16)mg_sdk_resident_storage_path_exists(test_path);
    OUT[3] = 0x7401;
    return 1;
}
static int app_frame(mg_sdk_u32 ticks) { (void)ticks; return 1; }
static void app_stop(void) {}
static const struct mg_sdk_runtime_callbacks callbacks = { app_start, app_frame, app_stop };
int main(void) { mg_sdk_resident_run(&callbacks); for (;;) {} }
