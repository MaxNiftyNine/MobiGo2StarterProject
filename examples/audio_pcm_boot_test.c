#include "mobigo_sdk/mobigo_sdk.h"

/*
 * Research/validation application for the recovered resident audio-resource
 * ABI. All resource metadata and waveform bytes are authored here; no retail
 * sound data is used.
 */

#define AUDIO_ROOT ((volatile mg_sdk_u16 *)0x5a00UL)
#define AUDIO_W_RECORD ((volatile struct mg_sdk_audio_w_record *)0x5a20UL)
#define AUDIO_LAYOUT ((volatile mg_sdk_u16 *)0x5a60UL)
#define AUDIO_WAVE ((volatile mg_sdk_u16 *)0x5b00UL)
#define AUDIO_STATE ((volatile mg_sdk_u16 *)0x59d0UL)

enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_QUERY_RESULT = 3,
    ST_PLAY_STATE = 4,
    ST_RELOCATED_LO = 5,
    ST_RELOCATED_HI = 6,
    ST_FRAME_COUNT = 7
};

static void build_clean_audio(void)
{
    mg_sdk_u16 i;

    mg_sdk_audio_prepare_single_w_root(
        (mg_sdk_u16 *)AUDIO_ROOT, 0x00005a20UL, 0x00005a60UL);
    mg_sdk_audio_prepare_w_pcm8(
        (struct mg_sdk_audio_w_record *)AUDIO_W_RECORD,
        0x44, 4000, 64, 0);
    mg_sdk_audio_prepare_wave_layout(
        (mg_sdk_u16 *)AUDIO_LAYOUT, 0x00005b00UL, 34);

    /* 64 unsigned 8-bit square-wave samples, two samples per word. */
    for (i = 0; i < 32; ++i) {
        AUDIO_WAVE[i] = (i & 2) ? 0x4040 : 0xc0c0;
    }
    AUDIO_WAVE[32] = 0xffff; /* SPU one-shot terminator */
    AUDIO_WAVE[33] = 0x0000;
}

static int app_start(void)
{
    mg_sdk_u32 handle;
    mg_sdk_u16 state;

    AUDIO_STATE[ST_STATUS] = 0x7700;
    AUDIO_STATE[ST_HANDLE_LO] = 0xffff;
    AUDIO_STATE[ST_HANDLE_HI] = 0xffff;
    AUDIO_STATE[ST_QUERY_RESULT] = 0xffff;
    AUDIO_STATE[ST_PLAY_STATE] = 0xffff;
    AUDIO_STATE[ST_FRAME_COUNT] = 0;

    build_clean_audio();
    mg_sdk_resident_register_audio_resources((mg_sdk_u16 *)AUDIO_ROOT, 0);
    AUDIO_STATE[ST_STATUS] = 0x7701;
    AUDIO_STATE[ST_RELOCATED_LO] =
        AUDIO_W_RECORD->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_LO];
    AUDIO_STATE[ST_RELOCATED_HI] =
        AUDIO_W_RECORD->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_HI];

    handle = mg_sdk_resident_play_sound(3, 0x7f, 0x40, 0, 0);
    AUDIO_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
    AUDIO_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
    if (handle == 0xffffffffUL) {
        AUDIO_STATE[ST_STATUS] = 0xe701;
        return 1;
    }

    state = 0xffff;
    AUDIO_STATE[ST_QUERY_RESULT] =
        (mg_sdk_u16)mg_sdk_resident_get_sound_state(handle, &state);
    AUDIO_STATE[ST_PLAY_STATE] = state;
    AUDIO_STATE[ST_STATUS] = 0x7702;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    mg_sdk_u32 handle;
    mg_sdk_u16 state;
    (void)ticks;

    AUDIO_STATE[ST_FRAME_COUNT]++;
    handle = (mg_sdk_u32)AUDIO_STATE[ST_HANDLE_LO] |
        ((mg_sdk_u32)AUDIO_STATE[ST_HANDLE_HI] << 16);
    state = 0xffff;
    AUDIO_STATE[ST_QUERY_RESULT] =
        (mg_sdk_u16)mg_sdk_resident_get_sound_state(handle, &state);
    AUDIO_STATE[ST_PLAY_STATE] = state;
    if (AUDIO_STATE[ST_FRAME_COUNT] > 10) {
        AUDIO_STATE[ST_STATUS] = 0x7703;
    }
    return 1;
}

static void app_stop(void)
{
}

static const struct mg_sdk_runtime_callbacks callbacks = {
    app_start,
    app_frame,
    app_stop
};

int main(void)
{
    mg_sdk_resident_run(&callbacks);
    for (;;) {
    }
}
