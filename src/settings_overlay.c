#include "mobigo_sdk/settings_overlay.h"

void mg_sdk_settings_object_prepare(
    struct mg_sdk_settings_object *object,
    mg_sdk_s16 x,
    mg_sdk_s16 y)
{
    mg_sdk_ui_b_object_prepare(
        (struct mg_sdk_ui_b_object *)object,
        x,
        y,
        0);
}

void mg_sdk_settings_object_show(
    struct mg_sdk_settings_object *object,
    mg_sdk_u16 mode,
    mg_sdk_u16 record,
    mg_sdk_s16 x,
    mg_sdk_s16 y)
{
    mg_sdk_ui_b_object_show(
        (struct mg_sdk_ui_b_object *)object,
        mode,
        record,
        x,
        y);
}

void mg_sdk_settings_object_hide(struct mg_sdk_settings_object *object)
{
    mg_sdk_ui_b_object_hide((struct mg_sdk_ui_b_object *)object);
}
