#include "mobigo_sdk/ui_family_b.h"

void mg_sdk_ui_b_object_prepare(
    struct mg_sdk_ui_b_object *object,
    mg_sdk_s16 x,
    mg_sdk_s16 y,
    mg_sdk_u16 state_3)
{
    object->word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] = 0;
    object->word[MG_SDK_UI_B_OBJECT_WORD_X] = (mg_sdk_u16)x;
    object->word[MG_SDK_UI_B_OBJECT_WORD_Y] = (mg_sdk_u16)y;
    object->word[MG_SDK_UI_B_OBJECT_WORD_STATE_3] = state_3;
    object->word[MG_SDK_UI_B_OBJECT_WORD_STATE_7] = 1;
    object->word[MG_SDK_UI_B_OBJECT_WORD_STATE_8] = 0;
}

void mg_sdk_ui_b_object_show(
    struct mg_sdk_ui_b_object *object,
    mg_sdk_u16 mode,
    mg_sdk_u16 record,
    mg_sdk_s16 x,
    mg_sdk_s16 y)
{
    object->word[MG_SDK_UI_B_OBJECT_WORD_X] = (mg_sdk_u16)x;
    object->word[MG_SDK_UI_B_OBJECT_WORD_Y] = (mg_sdk_u16)y;
    object->word[MG_SDK_UI_B_OBJECT_WORD_MODE] = mode;
    object->word[MG_SDK_UI_B_OBJECT_WORD_RECORD] = record;
    object->word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] = 1;
}

void mg_sdk_ui_b_object_hide(struct mg_sdk_ui_b_object *object)
{
    object->word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] = 0;
}
