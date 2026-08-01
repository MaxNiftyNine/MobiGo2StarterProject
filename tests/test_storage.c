#include <assert.h>
#include <stddef.h>

#include "mobigo_sdk/resident_storage.h"

static void assert_zero_tail(const mg_sdk_u16 *words, size_t first)
{
    size_t i;
    for (i = first; i < MG_SDK_STORAGE_PATH_WORDS; ++i) {
        assert(words[i] == 0);
    }
}

int main(void)
{
    mg_sdk_u16 words[MG_SDK_STORAGE_PATH_WORDS];
    static const char retail_path[] = "A:DEGER\\MBASORT.LST";
    static const char exact_limit[] = "123456789012345678901234567";
    static const char too_long[] = "1234567890123456789012345678";

    assert(mg_sdk_storage_pack_path(words, retail_path) == 1);
    assert(words[0] == 0x3a41); /* "A:" */
    assert(words[1] == 0x4544); /* "DE" */
    assert(words[2] == 0x4547); /* "GE" */
    assert(words[3] == 0x5c52); /* "R\\" */
    assert(words[4] == 0x424d); /* "MB" */
    assert(words[5] == 0x5341); /* "AS" */
    assert(words[6] == 0x524f); /* "OR" */
    assert(words[7] == 0x2e54); /* "T." */
    assert(words[8] == 0x534c); /* "LS" */
    assert(words[9] == 0x0054); /* "T\\0" */
    assert_zero_tail(words, 10);

    assert(mg_sdk_storage_pack_path(words, "A:") == 1);
    assert(words[0] == 0x3a41);
    assert_zero_tail(words, 1);

    assert(mg_sdk_storage_pack_path(words, exact_limit) == 1);
    assert((words[13] & 0x00ff) == (mg_sdk_u16)'7');
    assert((words[13] & 0xff00) == 0);

    assert(mg_sdk_storage_pack_path(words, too_long) == 0);
    assert(mg_sdk_storage_pack_path(0, retail_path) == 0);
    assert(mg_sdk_storage_pack_path(words, 0) == 0);
    return 0;
}
