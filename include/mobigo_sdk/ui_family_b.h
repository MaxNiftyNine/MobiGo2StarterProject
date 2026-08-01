#ifndef MOBIGO_SDK_UI_FAMILY_B_H
#define MOBIGO_SDK_UI_FAMILY_B_H

#include "mobigo_sdk/resource_bundle.h"

/*
 * Renderer-confirmed mutable prefix of a resident family-B object.
 *
 * The same layout is used by brightness, volume, and the application-requested
 * power-off presentation.  Service 0x075f18 returns this object after a
 * family-B handle has been created by 0x075f12.
 */
enum mg_sdk_ui_b_object_layout {
    MG_SDK_UI_B_OBJECT_WORD_VISIBLE = 0,
    MG_SDK_UI_B_OBJECT_WORD_X = 1,
    MG_SDK_UI_B_OBJECT_WORD_Y = 2,
    MG_SDK_UI_B_OBJECT_WORD_STATE_3 = 3,
    /* Renderer selects normal/horizontal/vertical/both coordinate flips. */
    MG_SDK_UI_B_OBJECT_WORD_ORIENTATION = 4,
    MG_SDK_UI_B_OBJECT_WORD_MODE = 5,
    MG_SDK_UI_B_OBJECT_WORD_RECORD = 6,
    /* Zero lets the resident timeline advance; one freezes/stops it. */
    MG_SDK_UI_B_OBJECT_WORD_ANIMATION_STOPPED = 7,
    /* Zero stops on the last record; nonzero wraps to record zero. */
    MG_SDK_UI_B_OBJECT_WORD_ANIMATION_LOOP = 8,
    /* Older working names retained as source-compatible aliases. */
    MG_SDK_UI_B_OBJECT_WORD_STATE_7 =
        MG_SDK_UI_B_OBJECT_WORD_ANIMATION_STOPPED,
    MG_SDK_UI_B_OBJECT_WORD_STATE_8 =
        MG_SDK_UI_B_OBJECT_WORD_ANIMATION_LOOP,
    /* Zero suppresses rendering; 1..0x3f program blending; >=0x40 is opaque. */
    MG_SDK_UI_B_OBJECT_WORD_OPACITY = 9,
    MG_SDK_UI_B_OBJECT_KNOWN_WORDS = 10
};

struct mg_sdk_ui_b_object {
    mg_sdk_u16 word[MG_SDK_UI_B_OBJECT_KNOWN_WORDS];
};

/*
 * Common object initialization observed in G1/SY. State word 3 is presentation
 * specific: standard brightness/volume use zero; G1's requested power-off
 * presentation sets it to one. Words not listed above remain untouched.
 */
void mg_sdk_ui_b_object_prepare(
    struct mg_sdk_ui_b_object *object,
    mg_sdk_s16 x,
    mg_sdk_s16 y,
    mg_sdk_u16 state_3);

void mg_sdk_ui_b_object_show(
    struct mg_sdk_ui_b_object *object,
    mg_sdk_u16 mode,
    mg_sdk_u16 record,
    mg_sdk_s16 x,
    mg_sdk_s16 y);

/*
 * Show and run a family-B mode from an explicit record. The resident advances
 * according to each record's duration, applies the destination record's X/Y
 * delta, and either stops on the final record or wraps according to `loop`.
 */
void mg_sdk_ui_b_object_play_animation(
    struct mg_sdk_ui_b_object *object,
    mg_sdk_u16 mode,
    mg_sdk_u16 record,
    mg_sdk_s16 x,
    mg_sdk_s16 y,
    mg_sdk_u16 loop);

void mg_sdk_ui_b_object_stop_animation(
    struct mg_sdk_ui_b_object *object);

void mg_sdk_ui_b_object_hide(struct mg_sdk_ui_b_object *object);

#endif
