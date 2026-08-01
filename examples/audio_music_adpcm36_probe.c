#include "mobigo_sdk/mobigo_sdk.h"
#include "clean_music_adpcm36.h"

/*
 * Clean generated ADPCM36 music-zone proof. The clean-room emulator
 * beat-counter patch delivers the hardware SPU IRQ4. All scheduling, resource
 * parsing, program/zone lookup, note setup, pitch calculation, voice
 * allocation, ADPCM36 decoding, and release remain resident/SPU behavior.
 */

#define MUSIC_STATE ((volatile mg_sdk_u16 *)0x5960UL)
#define AUDIO_ROOT ((volatile mg_sdk_u16 *)0x5a00UL)
#define MUSIC_RECORD ((volatile mg_sdk_u16 *)0x5a20UL)
#define AUDIO_LAYOUT ((volatile mg_sdk_u16 *)0x5a50UL)
#define PATCH_ROOT ((volatile mg_sdk_u16 *)0x5a60UL)

#define SPU17_WAVE_LO (*(volatile mg_sdk_u16 *)0x7d10UL)
#define SPU17_MODE (*(volatile mg_sdk_u16 *)0x7d11UL)
#define SPU17_PANVOL (*(volatile mg_sdk_u16 *)0x7d13UL)
#define SPU17_PREVIOUS (*(volatile mg_sdk_u16 *)0x7d19UL)
#define SPU17_CURRENT (*(volatile mg_sdk_u16 *)0x7d1bUL)
#define SPU17_FORMAT (*(volatile mg_sdk_u16 *)0x7d1dUL)
#define SPU17_PHASE_HI (*(volatile mg_sdk_u16 *)0x7f10UL)
#define SPU17_PITCH_LO (*(volatile mg_sdk_u16 *)0x7f14UL)
enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_WAVE_LO = 3,
    ST_WAVE_HI = 4,
    ST_INITIAL_STATE = 5,
    ST_FINAL_STATE = 6,
    ST_FRAME_COUNT = 7,
    ST_STOP_FRAME = 8,
    ST_PATCH_WORDS = 9,
    ST_FORMAT_SET = 10,
    ST_OBSERVED_WAVE_LO = 11,
    ST_OBSERVED_WAVE_HI = 12,
    ST_OBSERVED_MODE = 13,
    ST_OBSERVED_FORMAT = 14,
    ST_OBSERVED_PITCH_LO = 15,
    ST_OBSERVED_PITCH_HI = 16,
    ST_OBSERVED_PANVOL = 17,
    ST_SAW_POSITIVE = 18,
    ST_SAW_NEGATIVE = 19,
    ST_PHASE = 20
};

static mg_sdk_u32 current_handle(void)
{
    return (mg_sdk_u32)MUSIC_STATE[ST_HANDLE_LO] |
        ((mg_sdk_u32)MUSIC_STATE[ST_HANDLE_HI] << 16);
}

static void prepare_music_record(void)
{
    struct mg_sdk_audio_m_stream_writer writer;

    mg_sdk_audio_m_writer_init(
        &writer,
        (mg_sdk_u16 *)MUSIC_RECORD + MG_SDK_AUDIO_M_WORD_STREAM,
        16);
    mg_sdk_audio_m_write_marker(&writer, 120);
    mg_sdk_audio_m_write_skip_word(&writer, 0xabcd);
    mg_sdk_audio_m_write_program_change(&writer, 0, 0);
    mg_sdk_audio_m_write_note(&writer, 0, 60, 100, 6);
    mg_sdk_audio_m_write_wait(&writer, 8);
    mg_sdk_audio_m_write_end(&writer);
    mg_sdk_audio_prepare_m_header((mg_sdk_u16 *)MUSIC_RECORD, writer.count);
}

static int app_start(void)
{
    mg_sdk_u32 resources[1];
    mg_sdk_u32 wave_address;

    MUSIC_STATE[ST_STATUS] = 0x7790;
    MUSIC_STATE[ST_FRAME_COUNT] = 0;
    MUSIC_STATE[ST_STOP_FRAME] = 0xffff;
    MUSIC_STATE[ST_PHASE] = 0;
    MUSIC_STATE[ST_SAW_POSITIVE] = 0;
    MUSIC_STATE[ST_SAW_NEGATIVE] = 0;
    wave_address = (mg_sdk_u32)clean_music_adpcm36_words;
    MUSIC_STATE[ST_WAVE_LO] = (mg_sdk_u16)wave_address;
    MUSIC_STATE[ST_WAVE_HI] = (mg_sdk_u16)(wave_address >> 16);

    resources[0] = 0x00005a20UL;
    mg_sdk_audio_prepare_root(
        (mg_sdk_u16 *)AUDIO_ROOT, 1, 0, 0, resources, 0x00005a50UL);
    prepare_music_record();
    mg_sdk_audio_prepare_wave_layout(
        (mg_sdk_u16 *)AUDIO_LAYOUT,
        wave_address,
        CLEAN_MUSIC_ADPCM36_WORD_COUNT);
    mg_sdk_audio_prepare_single_pcm8_patch_root(
        (mg_sdk_u16 *)PATCH_ROOT,
        0x00005a50UL,
        0,
        60,
        127,
        CLEAN_MUSIC_ADPCM36_SAMPLE_RATE,
        0,
        0,
        CLEAN_MUSIC_ADPCM36_ENVELOPE_WORD_OFFSET);
    MUSIC_STATE[ST_PATCH_WORDS] = MG_SDK_AUDIO_PATCH_SINGLE_PROGRAM_WORDS;
    MUSIC_STATE[ST_FORMAT_SET] = mg_sdk_audio_set_program_zone_format(
        (mg_sdk_u16 *)PATCH_ROOT,
        0,
        0,
        MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36);
    if (MUSIC_STATE[ST_FORMAT_SET] != 1) {
        MUSIC_STATE[ST_STATUS] = 0xe790;
        return 1;
    }
    mg_sdk_resident_register_audio_resources(
        (mg_sdk_u16 *)AUDIO_ROOT,
        (mg_sdk_u16 *)PATCH_ROOT);
    MUSIC_STATE[ST_STATUS] = 0x7791;
    return 1;
}

static void observe_spu(void)
{
    mg_sdk_u16 previous = SPU17_PREVIOUS;
    mg_sdk_u16 current = SPU17_CURRENT;

    if (previous == 0xb000 || current == 0xb000) {
        MUSIC_STATE[ST_SAW_POSITIVE] = 1;
    }
    if (previous == 0x5000 || current == 0x5000) {
        MUSIC_STATE[ST_SAW_NEGATIVE] = 1;
    }
}

static int app_frame(mg_sdk_u32 ticks)
{
    mg_sdk_u32 handle;
    mg_sdk_u16 state;
    (void)ticks;

    MUSIC_STATE[ST_FRAME_COUNT]++;
    if (MUSIC_STATE[ST_PHASE] == 0) {
        /* Allow one frame after registration, matching retail startup order. */
        MUSIC_STATE[ST_PHASE] = 1;
        return 1;
    }
    if (MUSIC_STATE[ST_PHASE] == 1) {
        handle = mg_sdk_resident_play_music(3, 0x7f, 0, 3);
        MUSIC_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
        state = 0xffff;
        mg_sdk_resident_get_music_state(handle, &state);
        MUSIC_STATE[ST_INITIAL_STATE] = state;
        MUSIC_STATE[ST_PHASE] = 2;
    } else {
        observe_spu();
        if (MUSIC_STATE[ST_OBSERVED_MODE] == 0 && SPU17_MODE != 0) {
            MUSIC_STATE[ST_OBSERVED_WAVE_LO] = SPU17_WAVE_LO;
            MUSIC_STATE[ST_OBSERVED_WAVE_HI] = SPU17_MODE & 0x003f;
            MUSIC_STATE[ST_OBSERVED_MODE] = SPU17_MODE;
            MUSIC_STATE[ST_OBSERVED_FORMAT] = SPU17_FORMAT;
            MUSIC_STATE[ST_OBSERVED_PITCH_LO] = SPU17_PITCH_LO;
            MUSIC_STATE[ST_OBSERVED_PITCH_HI] = SPU17_PHASE_HI & 0x0007;
            MUSIC_STATE[ST_OBSERVED_PANVOL] = SPU17_PANVOL;
        }
    }

    state = 0xffff;
    mg_sdk_resident_get_music_state(current_handle(), &state);
    MUSIC_STATE[ST_FINAL_STATE] = state;
    if ((state == 0 || state == 4) && MUSIC_STATE[ST_PHASE] == 2) {
        MUSIC_STATE[ST_STOP_FRAME] = MUSIC_STATE[ST_FRAME_COUNT];
        MUSIC_STATE[ST_PHASE] = 3;
        MUSIC_STATE[ST_STATUS] = 0x7792;
    } else if (MUSIC_STATE[ST_FRAME_COUNT] > 24 &&
               MUSIC_STATE[ST_STATUS] == 0x7791) {
        MUSIC_STATE[ST_STATUS] = 0xe791;
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
