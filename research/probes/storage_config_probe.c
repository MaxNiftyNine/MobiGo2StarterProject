#include "mobigo_sdk/mobigo_sdk.h"

#define PROBE_STATE ((volatile mg_sdk_u16 *)0x5980UL)
#define PROBE_DATA ((volatile mg_sdk_u16 *)0x59a0UL)

typedef int (*resident_storage_config_fn)(void *output);
#define RESIDENT_STORAGE_CONFIG \
    ((resident_storage_config_fn)MG_SDK_RESIDENT_GET_VOLUME_PREFIX)

static int probe_start(void)
{
    unsigned short i;
    for (i = 0; i < 40; ++i) {
        PROBE_DATA[i] = 0xeeee;
    }
    PROBE_STATE[0] = (mg_sdk_u16)RESIDENT_STORAGE_CONFIG((void *)PROBE_DATA);
    PROBE_STATE[1] = 0x7201;
    return 1;
}

static int probe_frame(mg_sdk_u32 ticks)
{
    (void)ticks;
    return 1;
}

static void probe_stop(void)
{
}

static const struct mg_sdk_runtime_callbacks callbacks = {
    probe_start,
    probe_frame,
    probe_stop
};

int main(void)
{
    mg_sdk_resident_run(&callbacks);
    for (;;) {
    }
}
