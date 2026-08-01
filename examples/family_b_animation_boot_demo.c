#include "mobigo_sdk/mobigo_sdk.h"
#include "mobigo_clean_animation_resources.h"

#define BUNDLE_RAM ((unsigned short *)0x5000UL)
#define ANIM_STATE ((volatile unsigned short *)0x58b0UL)

enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_INITIAL_X = 3,
    ST_INITIAL_RECORD = 4,
    ST_SAW_RECORD_1 = 5,
    ST_RECORD_1_X = 6,
    ST_FINAL_X = 7,
    ST_FINAL_RECORD = 8,
    ST_FRAMES = 9
};

static mg_sdk_ui_handle animation_handle;

static int app_start(void)
{
    struct mg_sdk_ui_b_object *object;

    ANIM_STATE[ST_STATUS] = 0x50a0;
    mobigo_clean_animation_copy_bundle(BUNDLE_RAM);
    mobigo_clean_animation_register(BUNDLE_RAM);
    animation_handle = mobigo_clean_animation_create();
    ANIM_STATE[ST_HANDLE_LO] = (mg_sdk_u16)animation_handle;
    ANIM_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(animation_handle >> 16);
    if (animation_handle == MG_SDK_INVALID_UI_HANDLE) {
        ANIM_STATE[ST_STATUS] = 0xe5a0;
        return 1;
    }
    object = (struct mg_sdk_ui_b_object *)mg_sdk_ui_b_get(animation_handle);
    mg_sdk_ui_b_object_prepare(object, 80, 120, 0);
    mg_sdk_ui_b_object_play_animation(object, 0, 0, 80, 120, 0);
    ANIM_STATE[ST_INITIAL_X] = object->word[MG_SDK_UI_B_OBJECT_WORD_X];
    ANIM_STATE[ST_INITIAL_RECORD] = object->word[MG_SDK_UI_B_OBJECT_WORD_RECORD];
    ANIM_STATE[ST_FRAMES] = 0;
    ANIM_STATE[ST_STATUS] = 0x50a1;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    struct mg_sdk_ui_b_object *object;
    (void)ticks;

    object = (struct mg_sdk_ui_b_object *)mg_sdk_ui_b_get(animation_handle);
    ANIM_STATE[ST_FRAMES]++;
    ANIM_STATE[ST_FINAL_X] = object->word[MG_SDK_UI_B_OBJECT_WORD_X];
    ANIM_STATE[ST_FINAL_RECORD] = object->word[MG_SDK_UI_B_OBJECT_WORD_RECORD];
    if (object->word[MG_SDK_UI_B_OBJECT_WORD_RECORD] == 1) {
        ANIM_STATE[ST_SAW_RECORD_1] = 1;
        ANIM_STATE[ST_RECORD_1_X] = object->word[MG_SDK_UI_B_OBJECT_WORD_X];
        ANIM_STATE[ST_STATUS] = 0x50a2;
    }
    if (ANIM_STATE[ST_FRAMES] > 120 && ANIM_STATE[ST_SAW_RECORD_1] == 0) {
        ANIM_STATE[ST_STATUS] = 0xe5a1;
    }
    return 1;
}

static void app_stop(void) {}

static const struct mg_sdk_runtime_callbacks callbacks = {
    app_start, app_frame, app_stop
};

int main(void)
{
    mg_sdk_resident_run(&callbacks);
    for (;;) {}
}
