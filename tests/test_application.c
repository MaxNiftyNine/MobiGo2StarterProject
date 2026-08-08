#include <assert.h>
#include <string.h>

#include "mobigo_sdk/application.h"

/* application.c delegates the public predicate to this storage wrapper; the
 * path-packing unit test does not enter the target resident call. */
int mg_sdk_resident_storage_path_exists(const char *path)
{
    (void)path;
    return 0;
}

int main(void)
{
    mg_sdk_u16 words[MG_SDK_LAUNCH_PATH_WORDS];
    char exact[MG_SDK_LAUNCH_PATH_MAX_CHARS + 1];
    char too_long[MG_SDK_LAUNCH_PATH_MAX_CHARS + 2];
    int i;

    assert(mg_sdk_launch_pack_path(words, "A:\\B\\T.MBA"));
    assert(words[0] == (mg_sdk_u16)('A' | (':' << 8)));
    assert(words[1] == (mg_sdk_u16)('\\' | ('B' << 8)));

    for (i = 0; i < MG_SDK_LAUNCH_PATH_MAX_CHARS; ++i) {
        exact[i] = (char)('A' + (i % 26));
        too_long[i] = exact[i];
    }
    exact[MG_SDK_LAUNCH_PATH_MAX_CHARS] = '\0';
    too_long[MG_SDK_LAUNCH_PATH_MAX_CHARS] = 'Z';
    too_long[MG_SDK_LAUNCH_PATH_MAX_CHARS + 1] = '\0';
    assert(mg_sdk_launch_pack_path(words, exact));
    assert(!mg_sdk_launch_pack_path(words, too_long));
    assert(!mg_sdk_launch_pack_path(0, exact));
    assert(!mg_sdk_launch_pack_path(words, 0));
    return 0;
}
