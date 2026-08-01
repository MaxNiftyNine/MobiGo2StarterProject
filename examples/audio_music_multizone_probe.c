#include "mobigo_sdk/mobigo_sdk.h"

/*
 * Runtime proof for the generalized patch-bank builder: two melodic
 * programs, three melodic zones, one direct-note percussion entry, four
 * original PCM8 waveforms, and four separate M resources.
 *
 * The clean-room emulator beat-counter patch delivers the hardware SPU IRQ4,
 * so the title never calls resident internals. Sequence timing, patch lookup,
 * note decoding, and SPU setup all run through the official resident path.
 */

#define MUSIC_STATE ((volatile mg_sdk_u16 *)0x5980UL)
#define AUDIO_ROOT ((volatile mg_sdk_u16 *)0x5a00UL)
#define MUSIC_RECORD_0 ((volatile mg_sdk_u16 *)0x5a20UL)
#define MUSIC_RECORD_1 ((volatile mg_sdk_u16 *)0x5a40UL)
#define MUSIC_RECORD_2 ((volatile mg_sdk_u16 *)0x5a60UL)
#define MUSIC_RECORD_3 ((volatile mg_sdk_u16 *)0x5a80UL)
#define AUDIO_LAYOUT ((volatile mg_sdk_u16 *)0x5aa0UL)
#define PATCH_ROOT ((volatile mg_sdk_u16 *)0x5ab0UL)

enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_WAVE_0_LO = 3,
    ST_WAVE_0_HI = 4,
    ST_WAVE_1_LO = 5,
    ST_WAVE_1_HI = 6,
    ST_WAVE_2_LO = 7,
    ST_WAVE_2_HI = 8,
    ST_FIRST_STATE = 9,
    ST_PLAY_STATE = 10,
    ST_FRAME_COUNT = 11,
    ST_STOP_FRAME = 12,
    ST_PATCH_WORDS = 13,
    ST_PHASE = 14,
    ST_FIRST_STOP_FRAME = 15,
    ST_SECOND_FIRST_STATE = 16,
    ST_SECOND_STOP_FRAME = 17,
    ST_THIRD_FIRST_STATE = 18,
    ST_FIRST_OBSERVED_WAVE_LO = 19,
    ST_FIRST_OBSERVED_WAVE_HI = 20,
    ST_FIRST_OBSERVED_MODE = 21,
    ST_FIRST_OBSERVED_PITCH_LO = 22,
    ST_FIRST_OBSERVED_PITCH_HI = 23,
    ST_FIRST_OBSERVED_PANVOL = 24,
    ST_WAVE_3_LO = 25,
    ST_WAVE_3_HI = 26,
    ST_FOURTH_FIRST_STATE = 27,
    ST_THIRD_STOP_FRAME = 28,
    ST_HANDLE_0_LO = 29,
    ST_HANDLE_0_HI = 30,
    ST_HANDLE_1_LO = 31,
    ST_HANDLE_1_HI = 32,
    ST_HANDLE_2_LO = 33,
    ST_HANDLE_2_HI = 34,
    ST_HANDLE_3_LO = 35,
    ST_HANDLE_3_HI = 36
};

#define SPU17_WAVE_LO (*(volatile mg_sdk_u16 *)0x7d10UL)
#define SPU17_MODE (*(volatile mg_sdk_u16 *)0x7d11UL)
#define SPU17_PANVOL (*(volatile mg_sdk_u16 *)0x7d13UL)
#define SPU17_PHASE_HI (*(volatile mg_sdk_u16 *)0x7f10UL)
#define SPU17_PITCH_LO (*(volatile mg_sdk_u16 *)0x7f14UL)

/*
 * Four 64-byte unsigned PCM waveforms, each followed by an in-band terminator
 * and padding. Their two-word hold envelopes follow at word offsets
 * 136/138/140/142.
 */
static const mg_sdk_u16 clean_patch_payload[] = {
    /* Zone 0: square wave. */
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xffff,0x0000,
    /* Zone 1: narrower pulse wave. */
    0xd0d0,0x3030,0x3030,0x3030,0xd0d0,0x3030,0x3030,0x3030,
    0xd0d0,0x3030,0x3030,0x3030,0xd0d0,0x3030,0x3030,0x3030,
    0xd0d0,0x3030,0x3030,0x3030,0xd0d0,0x3030,0x3030,0x3030,
    0xd0d0,0x3030,0x3030,0x3030,0xd0d0,0x3030,0x3030,0x3030,
    0xffff,0x0000,
    /* Program 7: saw-like stepped wave. */
    0x2010,0x4030,0x6050,0x8070,0xa090,0xc0b0,0xe0d0,0x00f0,
    0x2010,0x4030,0x6050,0x8070,0xa090,0xc0b0,0xe0d0,0x00f0,
    0x2010,0x4030,0x6050,0x8070,0xa090,0xc0b0,0xe0d0,0x00f0,
    0x2010,0x4030,0x6050,0x8070,0xa090,0xc0b0,0xe0d0,0x00f0,
    0xffff,0x0000,
    /* Percussion note 36: alternating impulse-like pattern. */
    0xf020,0x2080,0x2040,0x2020,0xf020,0x2080,0x2040,0x2020,
    0xf020,0x2080,0x2040,0x2020,0xf020,0x2080,0x2040,0x2020,
    0xf020,0x2080,0x2040,0x2020,0xf020,0x2080,0x2040,0x2020,
    0xf020,0x2080,0x2040,0x2020,0xf020,0x2080,0x2040,0x2020,
    0xffff,0x0000,
    /* Envelope 0, envelope 1, envelope 2, percussion envelope. */
    0x7f7f,0x00ff,
    0x7f7f,0x00ff,
    0x7f7f,0x00ff,
    0x7f7f,0x00ff
};

static void prepare_patch_root(mg_sdk_u32 wave_base)
{
    struct mg_sdk_audio_pcm8_zone_spec zones_0[2];
    struct mg_sdk_audio_pcm8_zone_spec zones_7[1];
    struct mg_sdk_audio_pcm8_program_spec programs[2];
    struct mg_sdk_audio_pcm8_percussion_spec percussion[1];
    struct mg_sdk_audio_pcm8_patch_bank_spec bank;

    zones_0[0].root_key = 60;
    zones_0[0].upper_key = 65;
    zones_0[0].sample_rate = 4000;
    zones_0[0].sample_byte_offset = 0;
    zones_0[0].loop_word_offset = 0;
    zones_0[0].envelope_word_offset = 136;
    zones_0[1].root_key = 72;
    zones_0[1].upper_key = 127;
    zones_0[1].sample_rate = 6000;
    zones_0[1].sample_byte_offset = 68;
    zones_0[1].loop_word_offset = 34;
    zones_0[1].envelope_word_offset = 138;
    zones_7[0].root_key = 60;
    zones_7[0].upper_key = 127;
    zones_7[0].sample_rate = 8000;
    zones_7[0].sample_byte_offset = 136;
    zones_7[0].loop_word_offset = 68;
    zones_7[0].envelope_word_offset = 140;
    programs[0].program = 0;
    programs[0].zone = zones_0;
    programs[0].zone_count = 2;
    programs[1].program = 7;
    programs[1].zone = zones_7;
    programs[1].zone_count = 1;
    percussion[0].note = 36;
    percussion[0].sample_rate = 5000;
    percussion[0].sample_byte_offset = 204;
    percussion[0].loop_word_offset = 102;
    percussion[0].envelope_word_offset = 142;
    bank.program = programs;
    bank.program_count = 2;
    bank.percussion = percussion;
    bank.percussion_count = 1;

    MUSIC_STATE[ST_PATCH_WORDS] = mg_sdk_audio_prepare_pcm8_patch_bank(
        (mg_sdk_u16 *)PATCH_ROOT,
        188,
        0x00005aa0UL,
        &bank);
    mg_sdk_audio_prepare_wave_layout(
        (mg_sdk_u16 *)AUDIO_LAYOUT,
        wave_base,
        sizeof(clean_patch_payload));
}

static void prepare_music_record(
    volatile mg_sdk_u16 *record,
    mg_sdk_u16 channel,
    mg_sdk_u16 program,
    mg_sdk_u16 note,
    mg_sdk_u16 velocity)
{
    struct mg_sdk_audio_m_stream_writer writer;
    mg_sdk_audio_m_writer_init(
        &writer,
        (mg_sdk_u16 *)record + MG_SDK_AUDIO_M_WORD_STREAM,
        16);
    mg_sdk_audio_m_write_marker(&writer, 120);
    mg_sdk_audio_m_write_program_change(&writer, channel, program);
    mg_sdk_audio_m_write_note(&writer, channel, note, velocity, 6);
    mg_sdk_audio_m_write_wait(&writer, 8);
    mg_sdk_audio_m_write_end(&writer);
    mg_sdk_audio_prepare_m_header((mg_sdk_u16 *)record, writer.count);
}

static void prepare_music(void)
{
    mg_sdk_u32 resources[4];

    resources[0] = 0x00005a20UL;
    resources[1] = 0x00005a40UL;
    resources[2] = 0x00005a60UL;
    resources[3] = 0x00005a80UL;
    mg_sdk_audio_prepare_root(
        (mg_sdk_u16 *)AUDIO_ROOT, 4, 0, 0, resources, 0x00005aa0UL);
    prepare_music_record(MUSIC_RECORD_0, 0, 0, 60, 90);
    prepare_music_record(MUSIC_RECORD_1, 0, 0, 72, 100);
    prepare_music_record(MUSIC_RECORD_2, 0, 7, 60, 110);
    prepare_music_record(MUSIC_RECORD_3, 9, 0, 36, 120);
}

static int app_start(void)
{
    mg_sdk_u32 wave_base;

    MUSIC_STATE[ST_STATUS] = 0x7770;
    MUSIC_STATE[ST_FRAME_COUNT] = 0;
    MUSIC_STATE[ST_STOP_FRAME] = 0xffff;
    MUSIC_STATE[ST_FIRST_STOP_FRAME] = 0xffff;
    MUSIC_STATE[ST_SECOND_STOP_FRAME] = 0xffff;
    MUSIC_STATE[ST_THIRD_STOP_FRAME] = 0xffff;
    MUSIC_STATE[ST_PHASE] = 6;
    MUSIC_STATE[ST_FIRST_OBSERVED_WAVE_LO] = 0;
    MUSIC_STATE[ST_FIRST_OBSERVED_WAVE_HI] = 0;
    MUSIC_STATE[ST_FIRST_OBSERVED_MODE] = 0;
    MUSIC_STATE[ST_FIRST_OBSERVED_PITCH_LO] = 0;
    MUSIC_STATE[ST_FIRST_OBSERVED_PITCH_HI] = 0;
    MUSIC_STATE[ST_FIRST_OBSERVED_PANVOL] = 0;
    wave_base = (mg_sdk_u32)clean_patch_payload;
    MUSIC_STATE[ST_WAVE_0_LO] = (mg_sdk_u16)wave_base;
    MUSIC_STATE[ST_WAVE_0_HI] = (mg_sdk_u16)(wave_base >> 16);
    wave_base += 34;
    MUSIC_STATE[ST_WAVE_1_LO] = (mg_sdk_u16)wave_base;
    MUSIC_STATE[ST_WAVE_1_HI] = (mg_sdk_u16)(wave_base >> 16);
    wave_base += 34;
    MUSIC_STATE[ST_WAVE_2_LO] = (mg_sdk_u16)wave_base;
    MUSIC_STATE[ST_WAVE_2_HI] = (mg_sdk_u16)(wave_base >> 16);
    wave_base += 34;
    MUSIC_STATE[ST_WAVE_3_LO] = (mg_sdk_u16)wave_base;
    MUSIC_STATE[ST_WAVE_3_HI] = (mg_sdk_u16)(wave_base >> 16);
    wave_base -= 102;

    prepare_music();
    prepare_patch_root(wave_base);
    if (MUSIC_STATE[ST_PATCH_WORDS] != 188) {
        MUSIC_STATE[ST_STATUS] = 0xe770;
        return 1;
    }
    mg_sdk_resident_register_audio_resources(
        (mg_sdk_u16 *)AUDIO_ROOT, (mg_sdk_u16 *)PATCH_ROOT);
    MUSIC_STATE[ST_HANDLE_LO] = 0xffff;
    MUSIC_STATE[ST_HANDLE_HI] = 0xffff;
    MUSIC_STATE[ST_STATUS] = 0x7771;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    mg_sdk_u32 handle;
    mg_sdk_u16 state;
    mg_sdk_u16 phase;
    (void)ticks;

    MUSIC_STATE[ST_FRAME_COUNT]++;
    phase = MUSIC_STATE[ST_PHASE];
    if (phase == 6) {
        handle = mg_sdk_resident_play_music(3, 0x7f, 0, 3);
        MUSIC_STATE[ST_HANDLE_0_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_0_HI] = (mg_sdk_u16)(handle >> 16);
        MUSIC_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
        state = 0xffff;
        mg_sdk_resident_get_music_state(handle, &state);
        MUSIC_STATE[ST_FIRST_STATE] = state;
        MUSIC_STATE[ST_PHASE] = 0;
    } else if (phase == 1) {
        handle = mg_sdk_resident_play_music(4, 0x7f, 0, 3);
        MUSIC_STATE[ST_HANDLE_1_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_1_HI] = (mg_sdk_u16)(handle >> 16);
        MUSIC_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
        state = 0xffff;
        mg_sdk_resident_get_music_state(handle, &state);
        MUSIC_STATE[ST_SECOND_FIRST_STATE] = state;
        MUSIC_STATE[ST_PHASE] = 2;
    } else if (phase == 3) {
        handle = mg_sdk_resident_play_music(5, 0x7f, 0, 3);
        MUSIC_STATE[ST_HANDLE_2_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_2_HI] = (mg_sdk_u16)(handle >> 16);
        MUSIC_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
        state = 0xffff;
        mg_sdk_resident_get_music_state(handle, &state);
        MUSIC_STATE[ST_THIRD_FIRST_STATE] = state;
        MUSIC_STATE[ST_PHASE] = 4;
    } else if (phase == 7) {
        handle = mg_sdk_resident_play_music(6, 0x7f, 0, 3);
        MUSIC_STATE[ST_HANDLE_3_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_3_HI] = (mg_sdk_u16)(handle >> 16);
        MUSIC_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
        state = 0xffff;
        mg_sdk_resident_get_music_state(handle, &state);
        MUSIC_STATE[ST_FOURTH_FIRST_STATE] = state;
        MUSIC_STATE[ST_PHASE] = 8;
    } else {
        if (phase == 0 &&
            MUSIC_STATE[ST_FIRST_OBSERVED_WAVE_LO] == 0 &&
            MUSIC_STATE[ST_FIRST_OBSERVED_WAVE_HI] == 0) {
            MUSIC_STATE[ST_FIRST_OBSERVED_WAVE_LO] = SPU17_WAVE_LO;
            MUSIC_STATE[ST_FIRST_OBSERVED_WAVE_HI] = SPU17_MODE & 0x003f;
            MUSIC_STATE[ST_FIRST_OBSERVED_MODE] = SPU17_MODE;
            MUSIC_STATE[ST_FIRST_OBSERVED_PITCH_LO] = SPU17_PITCH_LO;
            MUSIC_STATE[ST_FIRST_OBSERVED_PITCH_HI] = SPU17_PHASE_HI & 0x0007;
            MUSIC_STATE[ST_FIRST_OBSERVED_PANVOL] = SPU17_PANVOL;
        }
    }
    handle = (mg_sdk_u32)MUSIC_STATE[ST_HANDLE_LO] |
        ((mg_sdk_u32)MUSIC_STATE[ST_HANDLE_HI] << 16);
    state = 0xffff;
    mg_sdk_resident_get_music_state(handle, &state);
    MUSIC_STATE[ST_PLAY_STATE] = state;
    phase = MUSIC_STATE[ST_PHASE];
    if ((state == 0 || state == 4) && phase == 0) {
        MUSIC_STATE[ST_FIRST_STOP_FRAME] = MUSIC_STATE[ST_FRAME_COUNT];
        MUSIC_STATE[ST_PHASE] = 1;
    } else if ((state == 0 || state == 4) && phase == 2) {
        MUSIC_STATE[ST_SECOND_STOP_FRAME] = MUSIC_STATE[ST_FRAME_COUNT];
        MUSIC_STATE[ST_PHASE] = 3;
    } else if ((state == 0 || state == 4) && phase == 4) {
        MUSIC_STATE[ST_THIRD_STOP_FRAME] = MUSIC_STATE[ST_FRAME_COUNT];
        MUSIC_STATE[ST_PHASE] = 7;
    } else if ((state == 0 || state == 4) && phase == 8) {
        MUSIC_STATE[ST_STOP_FRAME] = MUSIC_STATE[ST_FRAME_COUNT];
        MUSIC_STATE[ST_PHASE] = 5;
        MUSIC_STATE[ST_STATUS] = 0x7772;
    } else if (MUSIC_STATE[ST_FRAME_COUNT] > 48 &&
               MUSIC_STATE[ST_STATUS] == 0x7771) {
        MUSIC_STATE[ST_STATUS] = 0xe772;
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
