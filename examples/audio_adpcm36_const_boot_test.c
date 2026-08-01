#include "mobigo_sdk/mobigo_sdk.h"
#include "clean_adpcm_adpcm36.h"

/*
 * Clean generated ADPCM36 W proof. tools/verify/verify_adpcm36_emulator.py creates a
 * PCM WAV, converts it with build_adpcm36_audio.py, and links the generated
 * const translation unit through build_homebrew_mba_wine.py --extra-source.
 */

#define AUDIO_ROOT ((volatile mg_sdk_u16 *)0x5a00UL)
#define AUDIO_W_RECORD ((volatile struct mg_sdk_audio_w_record *)0x5a20UL)
#define AUDIO_LAYOUT ((volatile mg_sdk_u16 *)0x5a60UL)
#define AUDIO_STATE ((volatile mg_sdk_u16 *)0x59a0UL)

#define SPU0_MODE (*(volatile mg_sdk_u16 *)0x7c01UL)
#define SPU0_PREVIOUS (*(volatile mg_sdk_u16 *)0x7c09UL)
#define SPU0_CURRENT (*(volatile mg_sdk_u16 *)0x7c0bUL)
#define SPU0_FORMAT (*(volatile mg_sdk_u16 *)0x7c0dUL)
#define SPU0_PITCH_HIGH (*(volatile mg_sdk_u16 *)0x7e00UL)
#define SPU0_PITCH_LOW (*(volatile mg_sdk_u16 *)0x7e04UL)

enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_RELOCATED_LO = 3,
    ST_RELOCATED_HI = 4,
    ST_WAVE_ADDR_LO = 5,
    ST_WAVE_ADDR_HI = 6,
    ST_INITIAL_STATE = 7,
    ST_FINAL_STATE = 8,
    ST_STOP_FRAME = 9,
    ST_FRAME_COUNT = 10,
    ST_MODE = 11,
    ST_FORMAT = 12,
    ST_PITCH_LO = 13,
    ST_PITCH_HI = 14,
    ST_SAW_POSITIVE = 15,
    ST_SAW_NEGATIVE = 16,
    ST_LAST_PREVIOUS = 17,
    ST_LAST_CURRENT = 18
};

static mg_sdk_u32 current_handle(void)
{
    return (mg_sdk_u32)AUDIO_STATE[ST_HANDLE_LO] |
        ((mg_sdk_u32)AUDIO_STATE[ST_HANDLE_HI] << 16);
}

static void observe_samples(void)
{
    mg_sdk_u16 previous = SPU0_PREVIOUS;
    mg_sdk_u16 current = SPU0_CURRENT;
    AUDIO_STATE[ST_LAST_PREVIOUS] = previous;
    AUDIO_STATE[ST_LAST_CURRENT] = current;
    if (previous == 0xb000 || current == 0xb000) {
        AUDIO_STATE[ST_SAW_POSITIVE] = 1;
    }
    if (previous == 0x5000 || current == 0x5000) {
        AUDIO_STATE[ST_SAW_NEGATIVE] = 1;
    }
}

static int app_start(void)
{
    mg_sdk_u32 handle;
    mg_sdk_u32 wave_address;
    mg_sdk_u16 state;

    AUDIO_STATE[ST_STATUS] = 0x7780;
    AUDIO_STATE[ST_STOP_FRAME] = 0xffff;
    AUDIO_STATE[ST_FRAME_COUNT] = 0;
    AUDIO_STATE[ST_SAW_POSITIVE] = 0;
    AUDIO_STATE[ST_SAW_NEGATIVE] = 0;
    wave_address = (mg_sdk_u32)clean_adpcm_adpcm36_words;
    AUDIO_STATE[ST_WAVE_ADDR_LO] = (mg_sdk_u16)wave_address;
    AUDIO_STATE[ST_WAVE_ADDR_HI] = (mg_sdk_u16)(wave_address >> 16);

    mg_sdk_audio_prepare_single_w_root(
        (mg_sdk_u16 *)AUDIO_ROOT, 0x00005a20UL, 0x00005a60UL);
    mg_sdk_audio_prepare_w_adpcm36(
        (struct mg_sdk_audio_w_record *)AUDIO_W_RECORD,
        CLEAN_ADPCM_ADPCM36_STREAM_BYTE_COUNT,
        CLEAN_ADPCM_ADPCM36_SAMPLE_RATE,
        CLEAN_ADPCM_ADPCM36_SAMPLE_COUNT,
        0);
    mg_sdk_audio_prepare_wave_layout(
        (mg_sdk_u16 *)AUDIO_LAYOUT,
        wave_address,
        CLEAN_ADPCM_ADPCM36_WORD_COUNT);
    mg_sdk_resident_register_audio_resources((mg_sdk_u16 *)AUDIO_ROOT, 0);

    AUDIO_STATE[ST_RELOCATED_LO] =
        AUDIO_W_RECORD->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_LO];
    AUDIO_STATE[ST_RELOCATED_HI] =
        AUDIO_W_RECORD->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_HI];
    handle = mg_sdk_resident_play_sound(3, 0x7f, 0x40, 0, 0);
    AUDIO_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
    AUDIO_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
    state = 0xffff;
    mg_sdk_resident_get_sound_state(handle, &state);
    AUDIO_STATE[ST_INITIAL_STATE] = state;
    AUDIO_STATE[ST_MODE] = SPU0_MODE;
    AUDIO_STATE[ST_FORMAT] = SPU0_FORMAT;
    AUDIO_STATE[ST_PITCH_LO] = SPU0_PITCH_LOW;
    AUDIO_STATE[ST_PITCH_HI] = SPU0_PITCH_HIGH & 0x0007;
    observe_samples();
    AUDIO_STATE[ST_STATUS] =
        handle == 0xffffffffUL ? 0xe780 : 0x7781;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    mg_sdk_u16 state;
    (void)ticks;

    AUDIO_STATE[ST_FRAME_COUNT]++;
    observe_samples();
    state = 0xffff;
    mg_sdk_resident_get_sound_state(current_handle(), &state);
    AUDIO_STATE[ST_FINAL_STATE] = state;
    if ((state == 0 || state == 4) && AUDIO_STATE[ST_STOP_FRAME] == 0xffff) {
        AUDIO_STATE[ST_STOP_FRAME] = AUDIO_STATE[ST_FRAME_COUNT];
        AUDIO_STATE[ST_STATUS] = 0x7782;
    } else if (AUDIO_STATE[ST_FRAME_COUNT] > 20 &&
               AUDIO_STATE[ST_STATUS] == 0x7781) {
        AUDIO_STATE[ST_STATUS] = 0xe781;
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
