#include "mobigo_sdk/application.h"
#include "mobigo_sdk/resident_addresses.h"
#include "mobigo_sdk/resident_storage.h"

typedef int (*resident_path_exists_fn)(const mg_sdk_u16 *path);
typedef void (*resident_launch_mba_fn)(
    const mg_sdk_u16 *path,
    mg_sdk_u16 argument_count,
    const mg_sdk_u32 *arguments);

#define RESIDENT_PATH_EXISTS \
    ((resident_path_exists_fn)MG_SDK_RESIDENT_PATH_EXISTS)
#define RESIDENT_LAUNCH_MBA \
    ((resident_launch_mba_fn)MG_SDK_RESIDENT_LAUNCH_MBA)

int mg_sdk_resident_path_exists(const char *path)
{
    return mg_sdk_resident_storage_path_exists(path);
}

void mg_sdk_resident_launch_mba(
    const char *path,
    mg_sdk_u16 argument_count,
    const mg_sdk_u32 *arguments)
{
    mg_sdk_u16 packed[MG_SDK_STORAGE_PATH_WORDS];

    /*
     * The firmware also clamps this value. Repeating the clamp here documents
     * the recovered contract and prevents a future backend from exceeding it.
     */
    if (argument_count > MG_SDK_LAUNCH_MAX_ARGUMENTS) {
        argument_count = MG_SDK_LAUNCH_MAX_ARGUMENTS;
    }
    if (!mg_sdk_storage_pack_path(packed, path)) {
        return;
    }
    RESIDENT_LAUNCH_MBA(packed, argument_count, arguments);
}
