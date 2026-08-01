#include "mobigo_sdk/mobigo_sdk.h"

/*
 * Research proof for a completely clean M + patch-zone + PCM8 note.
 *
 * The clean-room patched emulator schedules the hardware SPU beat IRQ4. The
 * application uses only public resident registration/play/state services.
 */

#define MUSIC_STATE ((volatile mg_sdk_u16 *)0x5980UL)
#define AUDIO_ROOT ((volatile mg_sdk_u16 *)0x5a00UL)
#define MUSIC_RECORD ((volatile mg_sdk_u16 *)0x5a20UL)
#define AUDIO_LAYOUT ((volatile mg_sdk_u16 *)0x5a40UL)
#define PATCH_ROOT ((volatile mg_sdk_u16 *)0x5a50UL)
#define PATCH_GROUP (PATCH_ROOT + 20)
#define PATCH_ZONE (PATCH_GROUP + 6)

enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_WAVE_BASE_LO = 3,
    ST_WAVE_BASE_HI = 4,
    ST_FIRST_STATE = 5,
    ST_PLAY_STATE = 6,
    ST_FRAME_COUNT = 7,
    ST_STOP_FRAME = 8,
    ST_PHASE = 9
};

/*
 * 64 unsigned 8-bit square-wave samples, in-band SPU terminator/padding,
 * then a two-word envelope segment. The patch zone points its envelope
 * address at clean_patch_payload[34].
 */
static const mg_sdk_u16 clean_patch_payload[] = {
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xc0c0,0xc0c0,0x4040,0x4040,0xc0c0,0xc0c0,0x4040,0x4040,
    0xffff,0x0000,
    0x7f7f,0x00ff
};

static void prepare_patch_root(mg_sdk_u32 wave_base)
{
    mg_sdk_audio_prepare_single_pcm8_patch_root(
        (mg_sdk_u16 *)PATCH_ROOT,
        0x00005a40UL,
        0,
        60,
        60,
        4000,
        0,
        0,
        34);
    mg_sdk_audio_prepare_wave_layout(
        (mg_sdk_u16 *)AUDIO_LAYOUT,
        wave_base,
        sizeof(clean_patch_payload));
}

static void prepare_music(void)
{
    struct mg_sdk_audio_m_stream_writer writer;
    mg_sdk_u32 resources[1];

    resources[0] = 0x00005a20UL;
    mg_sdk_audio_prepare_root(
        (mg_sdk_u16 *)AUDIO_ROOT, 1, 0, 0, resources, 0x00005a40UL);
    mg_sdk_audio_m_writer_init(
        &writer,
        (mg_sdk_u16 *)MUSIC_RECORD + MG_SDK_AUDIO_M_WORD_STREAM,
        16);
    mg_sdk_audio_m_write_marker(&writer, 120);
    mg_sdk_audio_m_write_program_change(&writer, 0, 0);
    mg_sdk_audio_m_write_note(&writer, 0, 60, 100, 8);
    mg_sdk_audio_m_write_wait(&writer, 12);
    mg_sdk_audio_m_write_end(&writer);
    mg_sdk_audio_prepare_m_header((mg_sdk_u16 *)MUSIC_RECORD, writer.count);
}

static int app_start(void)
{
    mg_sdk_u32 wave_base;

    MUSIC_STATE[ST_STATUS] = 0x7760;
    MUSIC_STATE[ST_FRAME_COUNT] = 0;
    MUSIC_STATE[ST_STOP_FRAME] = 0xffff;
    MUSIC_STATE[ST_PHASE] = 0;
    wave_base = (mg_sdk_u32)clean_patch_payload;
    MUSIC_STATE[ST_WAVE_BASE_LO] = (mg_sdk_u16)wave_base;
    MUSIC_STATE[ST_WAVE_BASE_HI] = (mg_sdk_u16)(wave_base >> 16);
    prepare_music();
    prepare_patch_root(wave_base);
    mg_sdk_resident_register_audio_resources(
        (mg_sdk_u16 *)AUDIO_ROOT, (mg_sdk_u16 *)PATCH_ROOT);

    MUSIC_STATE[ST_STATUS] = 0x7760;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    mg_sdk_u32 handle;
    mg_sdk_u16 state;
    (void)ticks;

    MUSIC_STATE[ST_FRAME_COUNT]++;
    if (MUSIC_STATE[ST_PHASE] == 0) {
        MUSIC_STATE[ST_PHASE] = 1;
        return 1;
    }
    if (MUSIC_STATE[ST_PHASE] == 1) {
        handle = mg_sdk_resident_play_music(3, 0x7f, 0, 3);
        MUSIC_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
        MUSIC_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
        state = 0xffff;
        mg_sdk_resident_get_music_state(handle, &state);
        MUSIC_STATE[ST_FIRST_STATE] = state;
        MUSIC_STATE[ST_STATUS] =
            handle == 0xffffffffUL ? 0xe760 : 0x7761;
        MUSIC_STATE[ST_PHASE] = 2;
    }
    handle = (mg_sdk_u32)MUSIC_STATE[ST_HANDLE_LO] |
        ((mg_sdk_u32)MUSIC_STATE[ST_HANDLE_HI] << 16);
    state = 0xffff;
    mg_sdk_resident_get_music_state(handle, &state);
    MUSIC_STATE[ST_PLAY_STATE] = state;
    if ((state == 0 || state == 4) && MUSIC_STATE[ST_STOP_FRAME] == 0xffff) {
        MUSIC_STATE[ST_STOP_FRAME] = MUSIC_STATE[ST_FRAME_COUNT];
        MUSIC_STATE[ST_STATUS] = 0x7762;
    } else if (MUSIC_STATE[ST_FRAME_COUNT] > 80 && MUSIC_STATE[ST_STATUS] == 0x7761) {
        MUSIC_STATE[ST_STATUS] = 0xe761;
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
