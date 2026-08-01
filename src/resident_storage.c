#include "mobigo_sdk/resident_storage.h"
#include "mobigo_sdk/resident_addresses.h"

typedef mg_sdk_file_handle (*resident_file_open_fn)(
    const mg_sdk_u16 *path,
    mg_sdk_u16 mode);
typedef int (*resident_file_close_fn)(mg_sdk_file_handle handle);
typedef mg_sdk_u32 (*resident_file_read_fn)(
    void *destination,
    mg_sdk_u32 byte_count,
    mg_sdk_file_handle handle);
typedef mg_sdk_u32 (*resident_file_write_fn)(
    const void *source,
    mg_sdk_u32 byte_count,
    mg_sdk_file_handle handle);
typedef int (*resident_file_truncate_fn)(mg_sdk_file_handle handle);
typedef int (*resident_file_seek_fn)(
    mg_sdk_file_handle handle,
    mg_sdk_u32 byte_offset);
typedef mg_sdk_u32 (*resident_file_size_fn)(mg_sdk_file_handle handle);
typedef int (*resident_path_exists_fn)(const mg_sdk_u16 *path);
typedef int (*resident_path_remove_fn)(const mg_sdk_u16 *path);

#define RESIDENT_FILE_OPEN \
    ((resident_file_open_fn)MG_SDK_RESIDENT_FILE_OPEN)
#define RESIDENT_FILE_CLOSE \
    ((resident_file_close_fn)MG_SDK_RESIDENT_FILE_CLOSE)
#define RESIDENT_FILE_READ \
    ((resident_file_read_fn)MG_SDK_RESIDENT_FILE_READ)
#define RESIDENT_FILE_WRITE \
    ((resident_file_write_fn)MG_SDK_RESIDENT_FILE_WRITE)
#define RESIDENT_FILE_TRUNCATE \
    ((resident_file_truncate_fn)MG_SDK_RESIDENT_FILE_TRUNCATE)
#define RESIDENT_FILE_SEEK \
    ((resident_file_seek_fn)MG_SDK_RESIDENT_FILE_SEEK_ABSOLUTE)
#define RESIDENT_FILE_SIZE \
    ((resident_file_size_fn)MG_SDK_RESIDENT_FILE_SIZE)
#define RESIDENT_PATH_EXISTS \
    ((resident_path_exists_fn)MG_SDK_RESIDENT_PATH_EXISTS)
#define RESIDENT_PATH_REMOVE \
    ((resident_path_remove_fn)MG_SDK_RESIDENT_PATH_REMOVE)

int mg_sdk_storage_pack_path(
    mg_sdk_u16 *destination,
    const char *source)
{
    mg_sdk_u16 i;
    mg_sdk_u16 character;

    if (destination == 0 || source == 0) {
        return 0;
    }
    for (i = 0; i < MG_SDK_STORAGE_PATH_WORDS; ++i) {
        destination[i] = 0;
    }
    for (i = 0; i < MG_SDK_STORAGE_PATH_MAX_CHARS; ++i) {
        character = (mg_sdk_u16)source[i] & 0x00ff;
        if (character == 0) {
            return 1;
        }
        if ((i & 1) == 0) {
            destination[i >> 1] = character;
        }
        else {
            destination[i >> 1] |= character << 8;
        }
    }
    return ((mg_sdk_u16)source[MG_SDK_STORAGE_PATH_MAX_CHARS] & 0x00ff) == 0;
}

mg_sdk_file_handle mg_sdk_resident_file_open(
    const char *path,
    mg_sdk_u16 mode)
{
    mg_sdk_u16 packed[MG_SDK_STORAGE_PATH_WORDS];
    if (!mg_sdk_storage_pack_path(packed, path)) {
        return MG_SDK_INVALID_FILE_HANDLE;
    }
    return RESIDENT_FILE_OPEN(packed, mode);
}

int mg_sdk_resident_file_close(mg_sdk_file_handle handle)
{
    return RESIDENT_FILE_CLOSE(handle);
}

mg_sdk_u32 mg_sdk_resident_file_read(
    void *destination,
    mg_sdk_u32 byte_count,
    mg_sdk_file_handle handle)
{
    return RESIDENT_FILE_READ(destination, byte_count, handle);
}

mg_sdk_u32 mg_sdk_resident_file_write(
    const void *source,
    mg_sdk_u32 byte_count,
    mg_sdk_file_handle handle)
{
    return RESIDENT_FILE_WRITE(source, byte_count, handle);
}

int mg_sdk_resident_file_truncate(mg_sdk_file_handle handle)
{
    return RESIDENT_FILE_TRUNCATE(handle);
}

int mg_sdk_resident_file_seek_absolute(
    mg_sdk_file_handle handle,
    mg_sdk_u32 byte_offset)
{
    return RESIDENT_FILE_SEEK(handle, byte_offset);
}

mg_sdk_u32 mg_sdk_resident_file_size(mg_sdk_file_handle handle)
{
    return RESIDENT_FILE_SIZE(handle);
}

int mg_sdk_resident_storage_path_exists(const char *path)
{
    mg_sdk_u16 packed[MG_SDK_STORAGE_PATH_WORDS];
    if (!mg_sdk_storage_pack_path(packed, path)) {
        return 0;
    }
    return RESIDENT_PATH_EXISTS(packed);
}

int mg_sdk_resident_storage_path_remove(const char *path)
{
    mg_sdk_u16 packed[MG_SDK_STORAGE_PATH_WORDS];
    if (!mg_sdk_storage_pack_path(packed, path)) {
        return -1;
    }
    return RESIDENT_PATH_REMOVE(packed);
}
