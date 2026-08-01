#include <assert.h>

#include "mobigo_sdk/settings_overlay.h"

int main(void)
{
    struct mg_sdk_settings_object object = {{0xffff}};

    mg_sdk_settings_object_prepare(&object, 109, 214);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_VISIBLE] == 0);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_X] == 109);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_Y] == 214);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_STATE_3] == 0);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_STATE_7] == 1);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_STATE_8] == 0);

    mg_sdk_settings_object_show(&object, 1, 3, 138, 214);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_VISIBLE] == 1);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_X] == 138);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_Y] == 214);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_MODE] == 1);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_RECORD] == 3);

    mg_sdk_settings_object_hide(&object);
    assert(object.word[MG_SDK_SETTINGS_OBJECT_WORD_VISIBLE] == 0);
    return 0;
}
