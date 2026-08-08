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

int mg_sdk_launch_pack_path(
    mg_sdk_u16 *destination,
    const char *source)
{
    mg_sdk_u16 i;
    mg_sdk_u16 character;

    if (destination == 0 || source == 0) {
        return 0;
    }
    for (i = 0; i < MG_SDK_LAUNCH_PATH_WORDS; ++i) {
        destination[i] = 0;
    }
    for (i = 0; i < MG_SDK_LAUNCH_PATH_MAX_CHARS; ++i) {
        character = (mg_sdk_u16)source[i] & 0x00ffu;
        if (character == 0) {
            return 1;
        }
        if ((i & 1u) == 0) {
            destination[i >> 1] = character;
        } else {
            destination[i >> 1] |= (mg_sdk_u16)(character << 8);
        }
    }
    return ((mg_sdk_u16)source[MG_SDK_LAUNCH_PATH_MAX_CHARS] &
        0x00ffu) == 0;
}

void mg_sdk_resident_launch_mba(
    const char *path,
    mg_sdk_u16 argument_count,
    const mg_sdk_u32 *arguments)
{
    mg_sdk_u16 packed[MG_SDK_LAUNCH_PATH_WORDS];

    /*
     * The firmware also clamps this value. Repeating the clamp here documents
     * the recovered contract and prevents a future backend from exceeding it.
     */
    if (argument_count > MG_SDK_LAUNCH_MAX_ARGUMENTS) {
        argument_count = MG_SDK_LAUNCH_MAX_ARGUMENTS;
    }
    if (!mg_sdk_launch_pack_path(packed, path)) {
        return;
    }
    RESIDENT_LAUNCH_MBA(packed, argument_count, arguments);
}
