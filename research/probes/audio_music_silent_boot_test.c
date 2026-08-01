#include "mobigo_sdk/mobigo_sdk.h"

/*
 * Minimal clean M-resource proof. The stream deliberately contains no note
 * events, so it validates the sequencer grammar/state machine without needing
 * an instrument/patch bank: tempo -> wait -> end.
 */

#define MUSIC_STATE ((volatile mg_sdk_u16 *)0x59b0UL)
#define AUDIO_ROOT ((volatile mg_sdk_u16 *)0x5a00UL)
#define MUSIC_RECORD ((volatile mg_sdk_u16 *)0x5a20UL)
#define AUDIO_LAYOUT ((volatile mg_sdk_u16 *)0x5a40UL)
#define PATCH_ROOT ((volatile mg_sdk_u16 *)0x5a50UL)

enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_QUERY_RESULT = 3,
    ST_PLAY_STATE = 4,
    ST_FRAME_COUNT = 5,
    ST_STREAM_WORDS = 6,
    ST_FIRST_STATE = 7,
    ST_STOP_FRAME = 8
};

static void prepare_music_resources(void)
{
    struct mg_sdk_audio_m_stream_writer writer;
    mg_sdk_u32 resources[1];
    mg_sdk_u16 index;

    MUSIC_STATE[ST_STATUS] = 0x7740;
    MUSIC_STATE[ST_FRAME_COUNT] = 0;
    resources[0] = 0x00005a20UL;

    mg_sdk_audio_prepare_root(
        (mg_sdk_u16 *)AUDIO_ROOT, 1, 0, 0, resources, 0x00005a40UL);
    mg_sdk_audio_prepare_wave_layout((mg_sdk_u16 *)AUDIO_LAYOUT, 0, 0);
    for (index = 0; index < 14; ++index) {
        PATCH_ROOT[index] = 0;
    }
    PATCH_ROOT[2] = 0x5a40;
    mg_sdk_audio_m_writer_init(
        &writer,
        (mg_sdk_u16 *)MUSIC_RECORD + MG_SDK_AUDIO_M_WORD_STREAM,
        8);
    mg_sdk_audio_m_write_marker(&writer, 120);
    mg_sdk_audio_m_write_wait(&writer, 0x20);
    mg_sdk_audio_m_write_end(&writer);
    mg_sdk_audio_prepare_m_header((mg_sdk_u16 *)MUSIC_RECORD, writer.count);
    MUSIC_STATE[ST_STREAM_WORDS] = writer.count;

    mg_sdk_resident_register_audio_resources(
        (mg_sdk_u16 *)AUDIO_ROOT, (mg_sdk_u16 *)PATCH_ROOT);
}

static int app_start(void)
{
    mg_sdk_u32 handle;
    mg_sdk_u16 state;

    prepare_music_resources();
    MUSIC_STATE[ST_STOP_FRAME] = 0xffff;
    handle = mg_sdk_resident_play_music(3, 0x7f, 0, 3);
    MUSIC_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
    MUSIC_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
    state = 0xffff;
    MUSIC_STATE[ST_QUERY_RESULT] =
        (mg_sdk_u16)mg_sdk_resident_get_music_state(handle, &state);
    MUSIC_STATE[ST_FIRST_STATE] = state;
    MUSIC_STATE[ST_STATUS] =
        handle == 0xffffffffUL ? 0xe740 : 0x7741;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    mg_sdk_u32 handle;
    mg_sdk_u16 state;
    (void)ticks;

    MUSIC_STATE[ST_FRAME_COUNT]++;
    handle = (mg_sdk_u32)MUSIC_STATE[ST_HANDLE_LO] |
        ((mg_sdk_u32)MUSIC_STATE[ST_HANDLE_HI] << 16);
    state = 0xffff;
    MUSIC_STATE[ST_QUERY_RESULT] =
        (mg_sdk_u16)mg_sdk_resident_get_music_state(handle, &state);
    MUSIC_STATE[ST_PLAY_STATE] = state;
    if ((state == 0 || state == 4) && MUSIC_STATE[ST_STOP_FRAME] == 0xffff) {
        MUSIC_STATE[ST_STOP_FRAME] = MUSIC_STATE[ST_FRAME_COUNT];
        MUSIC_STATE[ST_STATUS] = 0x7742;
    } else if (MUSIC_STATE[ST_FRAME_COUNT] > 60 && MUSIC_STATE[ST_STATUS] == 0x7741) {
        MUSIC_STATE[ST_STATUS] = 0xe741;
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
