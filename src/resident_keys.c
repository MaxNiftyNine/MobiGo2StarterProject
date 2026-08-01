#include "mobigo_sdk/resident_keys.h"
#include "mobigo_sdk/resident_addresses.h"

typedef mg_sdk_u16 (*resident_get_keys_fn)(void);
typedef int (*resident_test_key_fn)(mg_sdk_u16 mask);

static mg_sdk_u16 get_keys(unsigned long address)
{
    return ((resident_get_keys_fn)address)();
}

static int test_key(unsigned long address, mg_sdk_u16 mask)
{
    return ((resident_test_key_fn)address)(mask);
}

mg_sdk_u16 mg_sdk_resident_system_keys(void)
{
    return get_keys(MG_SDK_RESIDENT_GET_SYSTEM_KEYS);
}

int mg_sdk_resident_system_key_down(mg_sdk_u16 mask)
{
    return test_key(MG_SDK_RESIDENT_SYSTEM_KEY_DOWN, mask);
}

int mg_sdk_resident_system_key_pressed(mg_sdk_u16 mask)
{
    return test_key(MG_SDK_RESIDENT_SYSTEM_KEY_PRESSED, mask);
}

int mg_sdk_resident_system_key_released(mg_sdk_u16 mask)
{
    return test_key(MG_SDK_RESIDENT_SYSTEM_KEY_RELEASED, mask);
}

mg_sdk_u16 mg_sdk_resident_game_keys(void)
{
    return get_keys(MG_SDK_RESIDENT_GET_GAME_KEYS);
}

int mg_sdk_resident_game_key_down(mg_sdk_u16 mask)
{
    return test_key(MG_SDK_RESIDENT_GAME_KEY_DOWN, mask);
}

int mg_sdk_resident_game_key_pressed(mg_sdk_u16 mask)
{
    return test_key(MG_SDK_RESIDENT_GAME_KEY_PRESSED, mask);
}

int mg_sdk_resident_game_key_released(mg_sdk_u16 mask)
{
    return test_key(MG_SDK_RESIDENT_GAME_KEY_RELEASED, mask);
}
