#include "mobigo_sdk/mobigo_sdk.h"

/*
 * Two original PCM8 W resources chained by one S resource. This exercises the
 * retail completion handler: W0 finishes, the same voice advances to W1, and
 * W1 then reaches the S terminator and stops.
 */

#define AUDIO_STATE ((volatile mg_sdk_u16 *)0x59c0UL)
#define AUDIO_ROOT ((volatile mg_sdk_u16 *)0x5a00UL)
#define AUDIO_W0 ((volatile struct mg_sdk_audio_w_record *)0x5a20UL)
#define AUDIO_W1 ((volatile struct mg_sdk_audio_w_record *)0x5a40UL)
#define AUDIO_LAYOUT ((volatile mg_sdk_u16 *)0x5a60UL)
#define AUDIO_S ((volatile mg_sdk_u16 *)0x5a70UL)

enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_WAVE_BASE_LO = 3,
    ST_WAVE_BASE_HI = 4,
    ST_W0_RELOC_LO = 5,
    ST_W0_RELOC_HI = 6,
    ST_W1_RELOC_LO = 7,
    ST_W1_RELOC_HI = 8,
    ST_QUERY_RESULT = 9,
    ST_PLAY_STATE = 10,
    ST_FRAME_COUNT = 11
};

enum {
    WAVE_WORDS_PER_CHILD = 34,
    WAVE_BYTES_PER_CHILD = WAVE_WORDS_PER_CHILD * 2
};

static const mg_sdk_u16 clean_waves[WAVE_WORDS_PER_CHILD * 2] = {
    /* Child 0: 4 kHz metadata, 64 unsigned 8-bit square-wave samples. */
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xffff,0x0000,

    /* Child 1: same authored waveform, 6 kHz metadata. */
    0x3030,0x3030,0xd0d0,0xd0d0,0x3030,0x3030,0xd0d0,0xd0d0,
    0x3030,0x3030,0xd0d0,0xd0d0,0x3030,0x3030,0xd0d0,0xd0d0,
    0x3030,0x3030,0xd0d0,0xd0d0,0x3030,0x3030,0xd0d0,0xd0d0,
    0x3030,0x3030,0xd0d0,0xd0d0,0x3030,0x3030,0xd0d0,0xd0d0,
    0xffff,0x0000
};

static int app_start(void)
{
    mg_sdk_u32 handle;
    mg_sdk_u32 wave_base;
    mg_sdk_u32 resources[3];
    mg_sdk_u16 children[2];

    AUDIO_STATE[ST_STATUS] = 0x7730;
    AUDIO_STATE[ST_FRAME_COUNT] = 0;
    wave_base = (mg_sdk_u32)clean_waves;
    AUDIO_STATE[ST_WAVE_BASE_LO] = (mg_sdk_u16)wave_base;
    AUDIO_STATE[ST_WAVE_BASE_HI] = (mg_sdk_u16)(wave_base >> 16);

    resources[0] = 0x00005a20UL; /* ID 3: W0 */
    resources[1] = 0x00005a40UL; /* ID 4: W1 */
    resources[2] = 0x00005a70UL; /* ID 5: S */
    mg_sdk_audio_prepare_root(
        (mg_sdk_u16 *)AUDIO_ROOT, 0, 2, 1, resources, 0x00005a60UL);
    mg_sdk_audio_prepare_w_pcm8(
        (struct mg_sdk_audio_w_record *)AUDIO_W0,
        WAVE_BYTES_PER_CHILD, 4000, 64, 0);
    mg_sdk_audio_prepare_w_pcm8(
        (struct mg_sdk_audio_w_record *)AUDIO_W1,
        WAVE_BYTES_PER_CHILD, 6000, 64, WAVE_BYTES_PER_CHILD);
    mg_sdk_audio_prepare_wave_layout(
        (mg_sdk_u16 *)AUDIO_LAYOUT,
        wave_base,
        WAVE_WORDS_PER_CHILD * 2);
    children[0] = 3;
    children[1] = 4;
    mg_sdk_audio_prepare_s_sequence((mg_sdk_u16 *)AUDIO_S, children, 2);

    mg_sdk_resident_register_audio_resources((mg_sdk_u16 *)AUDIO_ROOT, 0);
    AUDIO_STATE[ST_W0_RELOC_LO] =
        AUDIO_W0->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_LO];
    AUDIO_STATE[ST_W0_RELOC_HI] =
        AUDIO_W0->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_HI];
    AUDIO_STATE[ST_W1_RELOC_LO] =
        AUDIO_W1->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_LO];
    AUDIO_STATE[ST_W1_RELOC_HI] =
        AUDIO_W1->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_HI];

    /* Resource ID 5 is S; repeat=0 means stop at its ffffffff terminator. */
    handle = mg_sdk_resident_play_sound(5, 0x7f, 0x40, 0, 0);
    AUDIO_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
    AUDIO_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
    AUDIO_STATE[ST_STATUS] =
        handle == 0xffffffffUL ? 0xe730 : 0x7731;
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
    if (AUDIO_STATE[ST_FRAME_COUNT] > 10 && AUDIO_STATE[ST_STATUS] == 0x7731) {
        AUDIO_STATE[ST_STATUS] = 0x7732;
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
