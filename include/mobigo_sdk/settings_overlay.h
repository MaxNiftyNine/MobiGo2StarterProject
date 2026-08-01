#ifndef MOBIGO_SDK_SETTINGS_OVERLAY_H
#define MOBIGO_SDK_SETTINGS_OVERLAY_H

#include "mobigo_sdk/ui_family_b.h"

/*
 * Verified mutable fields in a resident family-B settings object.
 *
 * Official applications obtain this storage from service 0x075f18 after
 * creating their linked settings descriptor. Mode and record values are
 * bundle-local generated indices.
 */
enum mg_sdk_settings_object_layout {
    MG_SDK_SETTINGS_OBJECT_WORD_VISIBLE = MG_SDK_UI_B_OBJECT_WORD_VISIBLE,
    MG_SDK_SETTINGS_OBJECT_WORD_X = MG_SDK_UI_B_OBJECT_WORD_X,
    MG_SDK_SETTINGS_OBJECT_WORD_Y = MG_SDK_UI_B_OBJECT_WORD_Y,
    MG_SDK_SETTINGS_OBJECT_WORD_STATE_3 = MG_SDK_UI_B_OBJECT_WORD_STATE_3,
    MG_SDK_SETTINGS_OBJECT_WORD_ORIENTATION = MG_SDK_UI_B_OBJECT_WORD_ORIENTATION,
    MG_SDK_SETTINGS_OBJECT_WORD_MODE = MG_SDK_UI_B_OBJECT_WORD_MODE,
    MG_SDK_SETTINGS_OBJECT_WORD_RECORD = MG_SDK_UI_B_OBJECT_WORD_RECORD,
    MG_SDK_SETTINGS_OBJECT_WORD_STATE_7 = MG_SDK_UI_B_OBJECT_WORD_STATE_7,
    MG_SDK_SETTINGS_OBJECT_WORD_STATE_8 = MG_SDK_UI_B_OBJECT_WORD_STATE_8,
    MG_SDK_SETTINGS_OBJECT_WORD_OPACITY = MG_SDK_UI_B_OBJECT_WORD_OPACITY,
    MG_SDK_SETTINGS_OBJECT_KNOWN_WORDS = MG_SDK_UI_B_OBJECT_KNOWN_WORDS
};

struct mg_sdk_settings_object {
    mg_sdk_u16 word[MG_SDK_SETTINGS_OBJECT_KNOWN_WORDS];
};

/*
 * Prepare reproduces the one-time field initialization common to G1/SY.
 * Show selects one bundle-local record and makes it visible. Hide clears the
 * same visibility word used by the official timeout path.
 */
void mg_sdk_settings_object_prepare(
    struct mg_sdk_settings_object *object,
    mg_sdk_s16 x,
    mg_sdk_s16 y);

void mg_sdk_settings_object_show(
    struct mg_sdk_settings_object *object,
    mg_sdk_u16 mode,
    mg_sdk_u16 record,
    mg_sdk_s16 x,
    mg_sdk_s16 y);

void mg_sdk_settings_object_hide(struct mg_sdk_settings_object *object);

#endif
