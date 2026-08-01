#include "self_tests.h"

struct pure_fake {
    mg_sdk_u16 edge;
    mg_sdk_u16 volume;
    mg_sdk_u16 brightness;
    mg_sdk_u16 gain;
    mg_sdk_u16 backlight;
    mg_sdk_u16 posted;
    mg_sdk_u16 touch_received;
    mg_sdk_u32 now;
};

static int fake_edge(void *user, mg_sdk_u16 mask)
{
    struct pure_fake *fake = (struct pure_fake *)user;
    if ((fake->edge & mask) == 0) return 0;
    fake->edge &= (mg_sdk_u16)~mask;
    return 1;
}

static int fake_load_volume(void *user, mg_sdk_u16 *level)
{
    *level = ((struct pure_fake *)user)->volume;
    return 1;
}

static int fake_load_brightness(void *user, mg_sdk_u16 *level)
{
    *level = ((struct pure_fake *)user)->brightness;
    return 1;
}

static void fake_save_volume(void *user, mg_sdk_u16 level)
{
    ((struct pure_fake *)user)->volume = level;
}

static void fake_save_brightness(void *user, mg_sdk_u16 level)
{
    ((struct pure_fake *)user)->brightness = level;
}

static void fake_gain(void *user, mg_sdk_u16 value)
{
    ((struct pure_fake *)user)->gain = value;
}

static void fake_backlight(void *user, mg_sdk_u16 value)
{
    ((struct pure_fake *)user)->backlight = value;
}

static mg_sdk_u32 fake_ticks(void *user)
{
    return ((struct pure_fake *)user)->now;
}

static void fake_overlay(
    void *user, enum mg_sdk_overlay_kind kind, mg_sdk_u16 level,
    mg_sdk_u16 x, mg_sdk_u16 y)
{
    (void)user; (void)kind; (void)level; (void)x; (void)y;
}

static void fake_hide(void *user) { (void)user; }
static int fake_feedback(void *user, enum mg_sdk_feedback_kind kind)
{
    (void)user; (void)kind; return 1;
}
static int fake_feedback_active(void *user, int handle)
{
    (void)user; (void)handle; return 0;
}
static void fake_poweroff(void *user) { (void)user; }

static const struct mg_sdk_system_backend system_backend = {
    fake_edge, fake_load_volume, fake_save_volume, fake_gain,
    fake_load_brightness, fake_save_brightness, fake_backlight, fake_ticks,
    fake_overlay, fake_hide, fake_feedback, fake_feedback_active, fake_poweroff
};

static int input_first(void *user, mg_sdk_u16 *code)
{
    (void)user; *code = 0x41; return 1;
}
static int input_special(void *user, mg_sdk_u16 code)
{
    (void)user; return code == MG_SDK_SPECIAL_CODE_90;
}
static int input_game(void *user, mg_sdk_u16 mask)
{
    (void)user; return mask == MG_SDK_GAME_KEY_PRIMARY;
}
static int input_system(void *user, mg_sdk_u16 mask)
{
    (void)user; return mask == MG_SDK_KEY_OFF;
}
static void input_post(void *user, const struct mg_sdk_input_event *event)
{
    struct pure_fake *fake = (struct pure_fake *)user;
    if (event->x == -1 && event->y == -1) fake->posted++;
}
static const struct mg_sdk_input_backend input_backend = {
    input_first, input_special, input_game, input_system, input_post
};

static const mg_sdk_u16 touch_words[8] = {
    123, 45, 0xaaaa, 0xbbbb, 0xffff, 0xffff, 0, 0
};
static const mg_sdk_u16 *touch_data(void *user) { (void)user; return touch_words; }
static mg_sdk_u16 touch_count(void *user) { (void)user; return 2; }
static void touch_receive(void *user, const struct mg_sdk_touch_event *event)
{
    struct pure_fake *fake = (struct pure_fake *)user;
    if ((fake->touch_received == 0 && event->x == 123 && event->y == 45) ||
        (fake->touch_received == 1 &&
         event->state == MG_SDK_TOUCH_STATE_SENTINEL)) {
        fake->touch_received++;
    }
}
static const struct mg_sdk_touch_backend touch_backend = {
    touch_data, touch_count
};

mg_sdk_u16 hardware_run_pure_self_tests(void)
{
    mg_sdk_u16 failures = 0;
    mg_sdk_u16 words[16] = {0};
    mg_sdk_u16 pixels[8] = {0, 1, 2, 3, 3, 2, 1, 0};
    mg_sdk_u16 stream[24] = {0};
    mg_sdk_s16 samples[MG_SDK_ADPCM36_SAMPLES_PER_FRAME];
    mg_sdk_u16 encoded[MG_SDK_ADPCM36_FRAME_WORDS + MG_SDK_ADPCM36_END_WORDS];
    struct mg_sdk_audio_m_stream_writer writer;
    struct mg_sdk_ui_b_record record = {{0}};
    struct mg_sdk_component_reference component = {{0}};
    struct mg_sdk_bitmap_descriptor bitmap = {{0}};
    struct mg_sdk_bitmap_chunk chunk = {{0}};
    struct mg_sdk_ui_b_object object = {{0}};
    struct mg_sdk_system_controls controls;
    struct mg_sdk_input_pump pump;
    struct pure_fake fake = {0};
    mg_sdk_u16 index;

#define CHECK(value) do { if (!(value)) failures++; } while (0)

    mg_sdk_bundle_write_word_pair(words, 2, 0x12345678UL);
    CHECK(mg_sdk_bundle_read_word_pair(words, 2) == 0x12345678UL);
    CHECK(mg_sdk_bundle_primary_relative(0x100) == 0x80000100UL);
    CHECK(mg_sdk_bundle_secondary_relative(0x100) == 0xc0000100UL);
    CHECK(mg_sdk_bundle_auto_instance_table_words(3) == 12);
    mg_sdk_bundle_auto_instance_set_marker(words, 1, 1);
    CHECK(words[2] == 1 && words[3] == 0);

    mg_sdk_ui_b_record_build(
        &record, 2, -3, 12, -8, 8, -16, 16,
        0xffffffffUL, 0x120, 0x180);
    CHECK(mg_sdk_ui_b_record_delta_x(&record) == 2);
    CHECK(mg_sdk_ui_b_record_delta_y(&record) == -3);
    CHECK(mg_sdk_ui_b_record_duration(&record) == 12);
    mg_sdk_component_build(&component, -4, 5, 0x220);
    CHECK(mg_sdk_component_x_offset(&component) == -4);
    CHECK(mg_sdk_component_y_offset(&component) == 5);
    mg_sdk_bitmap_build(&bitmap,
        mg_sdk_bitmap_pack_format(MG_SDK_BITMAP_FORMAT_2BPP, 1, 0),
        32, 16, 0x300);
    CHECK(mg_sdk_bitmap_bits_per_pixel(&bitmap) == 2);
    CHECK(mg_sdk_bitmap_palette_selector(&bitmap) == 1);
    CHECK(mg_sdk_bitmap_chunk_build(
        &chunk, 32, 16, 0, mg_sdk_bundle_primary_relative(0x400)));
    CHECK(!mg_sdk_bitmap_chunk_build(
        &chunk, 8, 8, 0, mg_sdk_bundle_primary_relative(0x400)));
    CHECK(mg_sdk_bitmap_pack_2bpp_word(pixels) == 0xe41b);
    CHECK(mg_sdk_rgb555_pack(31, 31, 31, 0) == 0x7fff);

    mg_sdk_ui_b_object_prepare(&object, 40, 50, 0);
    mg_sdk_ui_b_object_play_animation(&object, 0, 0, 40, 50, 1);
    CHECK(object.word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] == 1);
    CHECK(object.word[MG_SDK_UI_B_OBJECT_WORD_ANIMATION_STOPPED] == 0);
    mg_sdk_ui_b_object_stop_animation(&object);
    mg_sdk_ui_b_object_hide(&object);
    CHECK(object.word[MG_SDK_UI_B_OBJECT_WORD_VISIBLE] == 0);

    mg_sdk_audio_m_writer_init(&writer, stream, 24);
    CHECK(mg_sdk_audio_m_write_marker(&writer, 120));
    CHECK(mg_sdk_audio_m_write_program_change(&writer, 0, 0));
    CHECK(mg_sdk_audio_m_write_control_change(&writer, 0, 7, 100));
    CHECK(mg_sdk_audio_m_write_skip_word(&writer, 0xabcd));
    CHECK(mg_sdk_audio_m_write_note(&writer, 0, 60, 100, 4));
    CHECK(mg_sdk_audio_m_write_wait(&writer, 8));
    CHECK(mg_sdk_audio_m_write_end(&writer));
    for (index = 0; index < MG_SDK_ADPCM36_SAMPLES_PER_FRAME; index++) {
        samples[index] = (index & 1) ? -12288 : 12288;
    }
    CHECK(mg_sdk_adpcm36_encode_frame(encoded, samples) <= 12);
    mg_sdk_adpcm36_finish(encoded + MG_SDK_ADPCM36_FRAME_WORDS);
    CHECK(encoded[MG_SDK_ADPCM36_FRAME_WORDS + 1] == 0xffff);
    CHECK(mg_sdk_sound_state_is_playing(2));
    CHECK(!mg_sdk_sound_state_is_playing(0));

    fake.volume = 7;
    fake.brightness = 2;
    mg_sdk_system_controls_init(&controls, &system_backend, &fake);
    CHECK(controls.volume == 7 && controls.brightness == 2);
    fake.edge = MG_SDK_KEY_VOLUME_UP;
    mg_sdk_system_controls_poll(&controls);
    CHECK(controls.volume == 8 && fake.gain == mg_sdk_volume_gain_table[8]);
    fake.edge = MG_SDK_KEY_BRIGHTNESS;
    mg_sdk_system_controls_poll(&controls);
    CHECK(controls.brightness == 3 &&
          fake.backlight == mg_sdk_backlight_table[3]);

    mg_sdk_input_init(&pump, &input_backend, &fake);
    mg_sdk_input_poll(&pump);
    CHECK(fake.posted == 4);
    mg_sdk_touch_poll(&touch_backend, &fake, touch_receive, &fake);
    CHECK(fake.touch_received == 2);

#undef CHECK
    return failures;
}
