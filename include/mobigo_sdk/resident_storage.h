#ifndef MOBIGO_SDK_RESIDENT_STORAGE_H
#define MOBIGO_SDK_RESIDENT_STORAGE_H

#include "mobigo_sdk/system_controls.h"

/*
 * Recovered resident file API.
 *
 * Public wrappers accept ordinary C strings. The raw resident ABI does not:
 * it consumes two 8-bit path characters packed into each 16-bit u'nSP word.
 * The resident backend has four simultaneous file slots and returns an 8-bit
 * slot plus an 8-bit generation counter as the public handle.
 */
typedef mg_sdk_u16 mg_sdk_file_handle;

enum mg_sdk_file_open_mode {
    MG_SDK_FILE_OPEN_READ = 1,
    MG_SDK_FILE_OPEN_WRITE = 2,
    /* EBOOK uses mode 3 for a DLC container it subsequently reads/updates. */
    MG_SDK_FILE_OPEN_READ_WRITE = 3
};

enum mg_sdk_storage_path_type {
    MG_SDK_STORAGE_PATH_MISSING = 0,
    MG_SDK_STORAGE_PATH_FILE = 1,
    MG_SDK_STORAGE_PATH_DIRECTORY = 2
};

enum {
    /* Resident path normalization consumes fourteen packed 16-bit words. */
    MG_SDK_STORAGE_PATH_WORDS = 14,
    MG_SDK_STORAGE_PATH_MAX_CHARS = 27
};

#define MG_SDK_INVALID_FILE_HANDLE ((mg_sdk_file_handle)0xffff)
#define MG_SDK_FILE_IO_ERROR ((mg_sdk_u32)0xffffffffUL)

/*
 * The target compiler stores C chars one per 16-bit word, while the resident
 * filesystem ABI consumes two 8-bit path characters per word. Public path
 * wrappers below perform this conversion automatically. This helper is also
 * available to other resident APIs that consume the same packed path form.
 */
int mg_sdk_storage_pack_path(
    mg_sdk_u16 *destination,
    const char *source);

mg_sdk_file_handle mg_sdk_resident_file_open(
    const char *path,
    mg_sdk_u16 mode);
int mg_sdk_resident_file_close(mg_sdk_file_handle handle);
mg_sdk_u32 mg_sdk_resident_file_read(
    void *destination,
    mg_sdk_u32 byte_count,
    mg_sdk_file_handle handle);
mg_sdk_u32 mg_sdk_resident_file_write(
    const void *source,
    mg_sdk_u32 byte_count,
    mg_sdk_file_handle handle);

/* Truncate to the current byte position. Returns 0 on observed success. */
int mg_sdk_resident_file_truncate(mg_sdk_file_handle handle);

/* Absolute byte offset. The retail backend rejects offsets beyond EOF. */
int mg_sdk_resident_file_seek_absolute(
    mg_sdk_file_handle handle,
    mg_sdk_u32 byte_offset);

/* Returns the file length in bytes, or MG_SDK_FILE_IO_ERROR on failure. */
mg_sdk_u32 mg_sdk_resident_file_size(mg_sdk_file_handle handle);

/*
 * Resident path predicate with automatic C-string packing. Observed results
 * are MG_SDK_STORAGE_PATH_MISSING/FILE/DIRECTORY.
 */
int mg_sdk_resident_storage_path_exists(const char *path);

/* Remove an existing file. Returns 0 on the verified successful path. */
int mg_sdk_resident_storage_path_remove(const char *path);

#endif
