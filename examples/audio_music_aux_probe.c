#include "mobigo_sdk/mobigo_sdk.h"

/* Verify the M 0x2/0x7/0x8 stream classes without assuming they are notes. */

#define AUX_STATE ((volatile mg_sdk_u16 *)0x5960UL)
#define AUDIO_ROOT ((volatile mg_sdk_u16 *)0x5a00UL)
#define MUSIC_RECORD ((volatile mg_sdk_u16 *)0x5a20UL)
#define AUDIO_LAYOUT ((volatile mg_sdk_u16 *)0x5a50UL)
#define PATCH_ROOT ((volatile mg_sdk_u16 *)0x5a60UL)
#define MUSIC_AUX_WORD_0 (*(volatile mg_sdk_u16 *)0x0397UL)
#define MUSIC_AUX_WORD_1 (*(volatile mg_sdk_u16 *)0x0398UL)

enum {
    ST_STATUS = 0,
    ST_HANDLE_LO = 1,
    ST_HANDLE_HI = 2,
    ST_INITIAL_STATE = 3,
    ST_FINAL_STATE = 4,
    ST_FRAME_COUNT = 5,
    ST_STOP_FRAME = 6,
    ST_AUX_WORD_0 = 7,
    ST_AUX_WORD_1 = 8,
    ST_PHASE = 9
};

static mg_sdk_u32 current_handle(void)
{
    return (mg_sdk_u32)AUX_STATE[ST_HANDLE_LO] |
        ((mg_sdk_u32)AUX_STATE[ST_HANDLE_HI] << 16);
}

static void prepare_music_record(void)
{
    struct mg_sdk_audio_m_stream_writer writer;
    mg_sdk_u16 aux_a[2];
    mg_sdk_u16 aux_b[2];

    aux_a[0] = 0x1234;
    aux_a[1] = 0x5678;
    aux_b[0] = 0x9abc;
    aux_b[1] = 0xdef0;
    mg_sdk_audio_m_writer_init(
        &writer,
        (mg_sdk_u16 *)MUSIC_RECORD + MG_SDK_AUDIO_M_WORD_STREAM,
        20);
    mg_sdk_audio_m_write_marker(&writer, 120);
    mg_sdk_audio_m_write_skip_word(&writer, 0xabcd);
    mg_sdk_audio_m_write_aux_cb(&writer, 3, 0x4567, aux_a, 2);
    mg_sdk_audio_m_write_aux(&writer, aux_b, 2);
    mg_sdk_audio_m_write_wait(&writer, 2);
    mg_sdk_audio_m_write_end(&writer);
    mg_sdk_audio_prepare_m_header((mg_sdk_u16 *)MUSIC_RECORD, writer.count);
}

static int app_start(void)
{
    mg_sdk_u32 resources[1];

    AUX_STATE[ST_STATUS] = 0x77a0;
    AUX_STATE[ST_FRAME_COUNT] = 0;
    AUX_STATE[ST_STOP_FRAME] = 0xffff;
    AUX_STATE[ST_PHASE] = 0;
    resources[0] = 0x00005a20UL;
    mg_sdk_audio_prepare_root(
        (mg_sdk_u16 *)AUDIO_ROOT, 1, 0, 0, resources, 0x00005a50UL);
    prepare_music_record();
    mg_sdk_audio_prepare_wave_layout((mg_sdk_u16 *)AUDIO_LAYOUT, 0, 0);
    mg_sdk_audio_prepare_empty_patch_root(
        (mg_sdk_u16 *)PATCH_ROOT, 0x00005a50UL);
    mg_sdk_resident_register_audio_resources(
        (mg_sdk_u16 *)AUDIO_ROOT, (mg_sdk_u16 *)PATCH_ROOT);
    AUX_STATE[ST_STATUS] = 0x77a1;
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    mg_sdk_u32 handle;
    mg_sdk_u16 state;
    (void)ticks;

    AUX_STATE[ST_FRAME_COUNT]++;
    if (AUX_STATE[ST_PHASE] == 0) {
        AUX_STATE[ST_PHASE] = 1;
        return 1;
    }
    if (AUX_STATE[ST_PHASE] == 1) {
        handle = mg_sdk_resident_play_music(3, 0x7f, 0, 3);
        AUX_STATE[ST_HANDLE_LO] = (mg_sdk_u16)handle;
        AUX_STATE[ST_HANDLE_HI] = (mg_sdk_u16)(handle >> 16);
        state = 0xffff;
        mg_sdk_resident_get_music_state(handle, &state);
        AUX_STATE[ST_INITIAL_STATE] = state;
        AUX_STATE[ST_PHASE] = 2;
    }
    AUX_STATE[ST_AUX_WORD_0] = MUSIC_AUX_WORD_0;
    AUX_STATE[ST_AUX_WORD_1] = MUSIC_AUX_WORD_1;
    state = 0xffff;
    mg_sdk_resident_get_music_state(current_handle(), &state);
    AUX_STATE[ST_FINAL_STATE] = state;
    if ((state == 0 || state == 4) && AUX_STATE[ST_PHASE] == 2) {
        AUX_STATE[ST_STOP_FRAME] = AUX_STATE[ST_FRAME_COUNT];
        AUX_STATE[ST_PHASE] = 3;
        AUX_STATE[ST_STATUS] = 0x77a2;
    } else if (AUX_STATE[ST_FRAME_COUNT] > 24 &&
               AUX_STATE[ST_STATUS] == 0x77a1) {
        AUX_STATE[ST_STATUS] = 0xe7a1;
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
