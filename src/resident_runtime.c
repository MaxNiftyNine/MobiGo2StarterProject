#include "mobigo_sdk/resident_runtime.h"
#include "mobigo_sdk/resident_addresses.h"

typedef int (*resident_runtime_setup_fn)(mg_sdk_u32 *reserved_scratch);
typedef int (*resident_runtime_step_fn)(
    const struct mg_sdk_runtime_callbacks *callbacks);
typedef void (*resident_runtime_finalize_fn)(void);

#define RESIDENT_RUNTIME_SETUP \
    ((resident_runtime_setup_fn)MG_SDK_RESIDENT_RUNTIME_SETUP)
#define RESIDENT_RUNTIME_STEP \
    ((resident_runtime_step_fn)MG_SDK_RESIDENT_RUNTIME_STEP)
#define RESIDENT_RUNTIME_FINALIZE \
    ((resident_runtime_finalize_fn)MG_SDK_RESIDENT_RUNTIME_FINALIZE)

int mg_sdk_resident_runtime_setup(mg_sdk_u32 *reserved_scratch)
{
    return RESIDENT_RUNTIME_SETUP(reserved_scratch);
}

int mg_sdk_resident_runtime_step(
    const struct mg_sdk_runtime_callbacks *callbacks)
{
    return RESIDENT_RUNTIME_STEP(callbacks);
}

void mg_sdk_resident_runtime_finalize(void)
{
    RESIDENT_RUNTIME_FINALIZE();
}

int mg_sdk_resident_run(
    const struct mg_sdk_runtime_callbacks *callbacks)
{
    mg_sdk_u32 scratch = 0;
    if (callbacks == 0 ||
        mg_sdk_resident_runtime_setup(&scratch) == 0) {
        return 0;
    }
    while (mg_sdk_resident_runtime_step(callbacks) != 0) {
    }
    mg_sdk_resident_runtime_finalize();
    return 1;
}
