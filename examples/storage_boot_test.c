#include "mobigo_sdk/mobigo_sdk.h"

#define APP_STATE ((volatile mg_sdk_u16 *)0x5900UL)
#define APP_BUFFER ((volatile mg_sdk_u16 *)0x5920UL)

enum {
    ST_STATUS = 0,
    ST_EXISTS_BEFORE = 1,
    ST_OPEN_WRITE = 2,
    ST_WRITE_LO = 3,
    ST_WRITE_HI = 4,
    ST_SIZE_WRITE_LO = 5,
    ST_SIZE_WRITE_HI = 6,
    ST_CLOSE_WRITE = 7,
    ST_EXISTS_AFTER = 8,
    ST_OPEN_READ = 9,
    ST_SIZE_READ_LO = 10,
    ST_SIZE_READ_HI = 11,
    ST_READ_LO = 12,
    ST_READ_HI = 13,
    ST_MATCH = 14,
    ST_SEEK_FOUR = 15,
    ST_READ_TAIL_LO = 16,
    ST_READ_TAIL_HI = 17,
    ST_TAIL_MATCH = 18,
    ST_CLOSE_READ = 19,
    ST_TRUNCATE_WRITE = 20
};

/* Existing stock file. The emulator run uses a disposable NAND copy. */
static const char test_path[] = "A:DEGER\\MBASORT.LST";
static const mg_sdk_u16 test_payload[4] = {
    0x1234, 0xabcd, 0x55aa, 0x0f0f
};

static void store_u32(unsigned short index, mg_sdk_u32 value)
{
    APP_STATE[index] = (mg_sdk_u16)value;
    APP_STATE[index + 1] = (mg_sdk_u16)(value >> 16);
}

static int match_words(unsigned short start, unsigned short count)
{
    unsigned short i;
    for (i = 0; i < count; ++i) {
        if (APP_BUFFER[i] != test_payload[start + i]) {
            return 0;
        }
    }
    return 1;
}

static int app_start(void)
{
    mg_sdk_u32 amount;
    mg_sdk_u32 size;
    mg_sdk_file_handle handle;
    unsigned short i;

    for (i = 0; i < 21; ++i) {
        APP_STATE[i] = 0xffff;
    }
    APP_STATE[ST_STATUS] = 0x7000;
    APP_STATE[ST_EXISTS_BEFORE] =
        (mg_sdk_u16)mg_sdk_resident_storage_path_exists(test_path);
    if (APP_STATE[ST_EXISTS_BEFORE] != MG_SDK_STORAGE_PATH_FILE) {
        APP_STATE[ST_STATUS] = 0xe700;
        return 1;
    }

    handle = mg_sdk_resident_file_open(test_path, MG_SDK_FILE_OPEN_WRITE);
    APP_STATE[ST_OPEN_WRITE] = handle;
    if (handle == MG_SDK_INVALID_FILE_HANDLE) {
        APP_STATE[ST_STATUS] = 0xe701;
        return 1;
    }
    APP_STATE[ST_STATUS] = 0x7010;

    APP_STATE[ST_TRUNCATE_WRITE] =
        (mg_sdk_u16)mg_sdk_resident_file_truncate(handle);
    if (APP_STATE[ST_TRUNCATE_WRITE] != 0) {
        APP_STATE[ST_STATUS] = 0xe70a;
        return 1;
    }

    for (i = 0; i < 4; ++i) {
        APP_BUFFER[i] = test_payload[i];
    }
    amount = mg_sdk_resident_file_write((const void *)APP_BUFFER, 8, handle);
    store_u32(ST_WRITE_LO, amount);
    if (amount != 8) {
        APP_STATE[ST_STATUS] = 0xe702;
        return 1;
    }
    size = mg_sdk_resident_file_size(handle);
    store_u32(ST_SIZE_WRITE_LO, size);
    if (size != 8) {
        APP_STATE[ST_STATUS] = 0xe703;
        return 1;
    }
    APP_STATE[ST_CLOSE_WRITE] =
        (mg_sdk_u16)mg_sdk_resident_file_close(handle);
    APP_STATE[ST_EXISTS_AFTER] =
        (mg_sdk_u16)mg_sdk_resident_storage_path_exists(test_path);
    if (APP_STATE[ST_EXISTS_AFTER] != MG_SDK_STORAGE_PATH_FILE) {
        APP_STATE[ST_STATUS] = 0xe704;
        return 1;
    }
    APP_STATE[ST_STATUS] = 0x7011;

    handle = mg_sdk_resident_file_open(test_path, MG_SDK_FILE_OPEN_READ);
    APP_STATE[ST_OPEN_READ] = handle;
    if (handle == MG_SDK_INVALID_FILE_HANDLE) {
        APP_STATE[ST_STATUS] = 0xe705;
        return 1;
    }
    size = mg_sdk_resident_file_size(handle);
    store_u32(ST_SIZE_READ_LO, size);
    if (size != 8) {
        APP_STATE[ST_STATUS] = 0xe706;
        return 1;
    }

    for (i = 0; i < 4; ++i) {
        APP_BUFFER[i] = 0;
    }
    amount = mg_sdk_resident_file_read((void *)APP_BUFFER, 8, handle);
    store_u32(ST_READ_LO, amount);
    APP_STATE[ST_MATCH] = (mg_sdk_u16)match_words(0, 4);
    if (amount != 8 || APP_STATE[ST_MATCH] == 0) {
        APP_STATE[ST_STATUS] = 0xe707;
        return 1;
    }

    APP_STATE[ST_SEEK_FOUR] =
        (mg_sdk_u16)mg_sdk_resident_file_seek_absolute(handle, 4);
    if (APP_STATE[ST_SEEK_FOUR] != 0) {
        APP_STATE[ST_STATUS] = 0xe708;
        return 1;
    }
    APP_BUFFER[0] = 0;
    APP_BUFFER[1] = 0;
    amount = mg_sdk_resident_file_read((void *)APP_BUFFER, 4, handle);
    store_u32(ST_READ_TAIL_LO, amount);
    APP_STATE[ST_TAIL_MATCH] = (mg_sdk_u16)match_words(2, 2);
    if (amount != 4 || APP_STATE[ST_TAIL_MATCH] == 0) {
        APP_STATE[ST_STATUS] = 0xe709;
        return 1;
    }

    APP_STATE[ST_CLOSE_READ] =
        (mg_sdk_u16)mg_sdk_resident_file_close(handle);
    APP_STATE[ST_STATUS] = 0x7001;
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
