#include <assert.h>
#include <stddef.h>

#include "mobigo_sdk/ui_family_b.h"

int main(void)
{
    struct mg_sdk_ui_b_object object = {{
        0xaaaa, 0xbbbb, 0xcccc, 0xdddd, 0xeeee,
        0xffff, 0x1111, 0x2222, 0x3333, 0x0040
    }};

    mg_sdk_ui_b_object_prepare(&object, 160, 120, 1);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] == 0);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_X] == 160);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_Y] == 120);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_STATE_3] == 1);
    assert(object.word[4] == 0xeeee);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_STATE_7] == 1);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_STATE_8] == 0);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_OPACITY] == 0x0040);

    mg_sdk_ui_b_object_show(&object, 2, 7, -4, 214);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] == 1);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_X] == (mg_sdk_u16)-4);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_Y] == 214);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_MODE] == 2);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_RECORD] == 7);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_ANIMATION_STOPPED] == 1);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_STATE_3] == 1);
    assert(object.word[4] == 0xeeee);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_OPACITY] == 0x0040);

    mg_sdk_ui_b_object_play_animation(&object, 2, 3, 40, 50, 1);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] == 1);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_MODE] == 2);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_RECORD] == 3);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_X] == 40);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_Y] == 50);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_ANIMATION_LOOP] == 1);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_ANIMATION_STOPPED] == 0);
    mg_sdk_ui_b_object_stop_animation(&object);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_ANIMATION_STOPPED] == 1);

    mg_sdk_ui_b_object_hide(&object);
    assert(object.word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] == 0);
    return 0;
}
