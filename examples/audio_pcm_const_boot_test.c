#include "mobigo_sdk/mobigo_sdk.h"

/*
 * Same clean resident PCM8 proof as audio_pcm_boot_test.c, but keep the large
 * waveform immutable in the MBA executable. Only the relocatable table/record
 * are copied/constructed in writable title RAM.
 */

#define AUDIO_ROOT ((volatile mg_sdk_u16 *)0x5a00UL)
#define AUDIO_W_RECORD ((volatile struct mg_sdk_audio_w_record *)0x5a20UL)
#define AUDIO_LAYOUT ((volatile mg_sdk_u16 *)0x5a60UL)
#define AUDIO_STATE ((volatile mg_sdk_u16 *)0x59d0UL)

enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_RELOCATED_LO = 3,
    ST_RELOCATED_HI = 4,
    ST_WAVE_ADDR_LO = 5,
    ST_WAVE_ADDR_HI = 6,
    ST_FRAME_COUNT = 7
};

static const mg_sdk_u16 clean_wave[] = {
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xffff,0x0000
};

static int app_start(void)
{
    mg_sdk_u32 handle;
    mg_sdk_u32 wave_address;

    AUDIO_STATE[ST_STATUS] = 0x7720;
    AUDIO_STATE[ST_FRAME_COUNT] = 0;
    wave_address = (mg_sdk_u32)clean_wave;
    AUDIO_STATE[ST_WAVE_ADDR_LO] = (mg_sdk_u16)wave_address;
    AUDIO_STATE[ST_WAVE_ADDR_HI] = (mg_sdk_u16)(wave_address >> 16);

    mg_sdk_audio_prepare_single_w_root(
        (mg_sdk_u16 *)AUDIO_ROOT, 0x00005a20UL, 0x00005a60UL);
    mg_sdk_audio_prepare_w_pcm8(
        (struct mg_sdk_audio_w_record *)AUDIO_W_RECORD,
        (mg_sdk_u32)sizeof(clean_wave) * 2, 4000, 64, 0);
    mg_sdk_audio_prepare_wave_layout(
        (mg_sdk_u16 *)AUDIO_LAYOUT,
        wave_address,
        sizeof(clean_wave) / sizeof(clean_wave[0]));
    mg_sdk_resident_register_audio_resources((mg_sdk_u16 *)AUDIO_ROOT, 0);

    AUDIO_STATE[ST_RELOCATED_LO] =
        AUDIO_W_RECORD->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_LO];
    AUDIO_STATE[ST_RELOCATED_HI] =
        AUDIO_W_RECORD->word[MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_HI];

    handle = mg_sdk_resident_play_sound(3, 0x7f, 0x40, 0, 0);
    AUDIO_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
    AUDIO_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
    AUDIO_STATE[ST_STATUS] =
        handle == 0xffffffffUL ? 0xe720 : 0x7721;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    (void)ticks;
    AUDIO_STATE[ST_FRAME_COUNT]++;
    if (AUDIO_STATE[ST_FRAME_COUNT] > 10 && AUDIO_STATE[ST_STATUS] == 0x7721) {
        AUDIO_STATE[ST_STATUS] = 0x7722;
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
