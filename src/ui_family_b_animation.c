#include "mobigo_sdk/ui_family_b.h"

void mg_sdk_ui_b_object_play_animation(
    struct mg_sdk_ui_b_object *object,
    mg_sdk_u16 mode,
    mg_sdk_u16 record,
    mg_sdk_s16 x,
    mg_sdk_s16 y,
    mg_sdk_u16 loop)
{
    object->word[MG_SDK_UI_B_OBJECT_WORD_X] = (mg_sdk_u16)x;
    object->word[MG_SDK_UI_B_OBJECT_WORD_Y] = (mg_sdk_u16)y;
    object->word[MG_SDK_UI_B_OBJECT_WORD_MODE] = mode;
    object->word[MG_SDK_UI_B_OBJECT_WORD_RECORD] = record;
    object->word[MG_SDK_UI_B_OBJECT_WORD_ANIMATION_LOOP] = loop != 0;
    object->word[MG_SDK_UI_B_OBJECT_WORD_ANIMATION_STOPPED] = 0;
    object->word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] = 1;
}

void mg_sdk_ui_b_object_stop_animation(
    struct mg_sdk_ui_b_object *object)
{
    object->word[MG_SDK_UI_B_OBJECT_WORD_ANIMATION_STOPPED] = 1;
}
