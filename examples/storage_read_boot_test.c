#include "mobigo_sdk/mobigo_sdk.h"

#define APP_STATE ((volatile mg_sdk_u16 *)0x5940UL)
#define APP_BUFFER ((volatile mg_sdk_u16 *)0x5960UL)

enum {
    ST_STATUS = 0,
    ST_HANDLE = 1,
    ST_SIZE_LO = 2,
    ST_SIZE_HI = 3,
    ST_READ0_LO = 4,
    ST_READ0_HI = 5,
    ST_MATCH0 = 6,
    ST_SEEK32 = 7,
    ST_READ32_LO = 8,
    ST_READ32_HI = 9,
    ST_MATCH32 = 10,
    ST_CLOSE = 11,
    ST_EXISTS = 12
};

static const char profile_path[] = "A:DEGER\\MBASORT.LST";

static void store_u32(unsigned short index, mg_sdk_u32 value)
{
    APP_STATE[index] = (mg_sdk_u16)value;
    APP_STATE[index + 1] = (mg_sdk_u16)(value >> 16);
}

static int match4(
    mg_sdk_u16 a,
    mg_sdk_u16 b,
    mg_sdk_u16 c,
    mg_sdk_u16 d)
{
    return APP_BUFFER[0] == a && APP_BUFFER[1] == b &&
        APP_BUFFER[2] == c && APP_BUFFER[3] == d;
}

static int app_start(void)
{
    mg_sdk_u32 amount;
    mg_sdk_u32 size;
    mg_sdk_file_handle handle;
    int seek_result;
    unsigned short i;

    for (i = 0; i < 13; ++i) {
        APP_STATE[i] = 0xffff;
    }
    APP_STATE[ST_STATUS] = 0x7100;

    APP_STATE[ST_EXISTS] = (mg_sdk_u16)mg_sdk_resident_path_exists(profile_path);
    if (APP_STATE[ST_EXISTS] != 1) {
        APP_STATE[ST_STATUS] = 0xe710;
        return 1;
    }

    handle = mg_sdk_resident_file_open(profile_path, MG_SDK_FILE_OPEN_READ);
    APP_STATE[ST_HANDLE] = handle;
    if (handle == MG_SDK_INVALID_FILE_HANDLE) {
        APP_STATE[ST_STATUS] = 0xe711;
        return 1;
    }
    APP_STATE[ST_STATUS] = 0x7110;

    size = mg_sdk_resident_file_size(handle);
    store_u32(ST_SIZE_LO, size);
    if (size != 38) {
        APP_STATE[ST_STATUS] = 0xe712;
        return 1;
    }
    for (i = 0; i < 4; ++i) {
        APP_BUFFER[i] = 0;
    }
    amount = mg_sdk_resident_file_read((void *)APP_BUFFER, 8, handle);
    store_u32(ST_READ0_LO, amount);
    APP_STATE[ST_MATCH0] = (mg_sdk_u16)match4(
        0x3030, 0x3230, 0x0a0d, 0x3430);
    if (amount != 8 || APP_STATE[ST_MATCH0] == 0) {
        APP_STATE[ST_STATUS] = 0xe713;
        return 1;
    }
    APP_STATE[ST_STATUS] = 0x7111;

    seek_result = mg_sdk_resident_file_seek_absolute(handle, 32);
    APP_STATE[ST_SEEK32] = (mg_sdk_u16)seek_result;
    if (seek_result != 0) {
        APP_STATE[ST_STATUS] = 0xe714;
        return 1;
    }
    for (i = 0; i < 4; ++i) {
        APP_BUFFER[i] = 0;
    }
    amount = mg_sdk_resident_file_read((void *)APP_BUFFER, 8, handle);
    store_u32(ST_READ32_LO, amount);
    APP_STATE[ST_MATCH32] = (mg_sdk_u16)match4(
        0x4142, 0x3120, 0x0a0d, 0x0000);
    if (amount != 6 || APP_STATE[ST_MATCH32] == 0) {
        APP_STATE[ST_STATUS] = 0xe715;
        return 1;
    }
    APP_STATE[ST_CLOSE] = (mg_sdk_u16)mg_sdk_resident_file_close(handle);
    APP_STATE[ST_STATUS] = 0x7101;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    (void)ticks;
    return 1;
}

static void app_stop(void)
{
}

static const struct mg_sdk_runtime_callbacks callbacks = {
    app_start,
    app_frame,
    app_stop
};

int main(void)
{
    mg_sdk_resident_run(&callbacks);
    for (;;) {
    }
}
