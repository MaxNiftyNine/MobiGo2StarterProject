#include "mobigo_sdk/mobigo_sdk.h"
#include "mobigo_clean_font_resources.h"
#include "hw_animation_resources.h"
#include "hw_primary_resources.h"
#include "self_tests.h"

/* All persistent writable state is placed explicitly because MBA entry does
 * not execute a conventional initialized-data CRT. These ranges stay inside
 * the title-RAM arena used by the SDK's resident-hardware regressions. */
#define PRIMARY_BUNDLE_RAM ((mg_sdk_u16 *)0x5000UL)
#define FONT_BUNDLE_RAM ((mg_sdk_u16 *)0x5400UL)
#define ANIMATION_BUNDLE_RAM ((mg_sdk_u16 *)0x5f20UL)
#define STATE ((volatile mg_sdk_u16 *)0x6000UL)
#define TEXT_HANDLES ((mg_sdk_ui_handle *)0x6100UL)
#define SYSTEM_CONTROLS ((struct mg_sdk_system_controls *)0x6180UL)

#define AUDIO_ROOT ((mg_sdk_u16 *)0x6200UL)
#define MUSIC_RECORD ((mg_sdk_u16 *)0x6220UL)
#define AUX_RECORD ((mg_sdk_u16 *)0x6240UL)
#define W_RECORD_0 ((struct mg_sdk_audio_w_record *)0x6260UL)
#define W_RECORD_1 ((struct mg_sdk_audio_w_record *)0x6280UL)
#define W_RECORD_ADPCM ((struct mg_sdk_audio_w_record *)0x62a0UL)
#define S_RECORD ((mg_sdk_u16 *)0x62c0UL)
#define AUDIO_LAYOUT ((mg_sdk_u16 *)0x62e0UL)
#define PATCH_ROOT ((mg_sdk_u16 *)0x6300UL)
#define AUDIO_WAVES ((mg_sdk_u16 *)0x6500UL)
#define IO_BUFFER ((mg_sdk_u16 *)0x6700UL)
#define MUSIC_AUX_WORD_0 (*(volatile mg_sdk_u16 *)0x0397UL)
#define MUSIC_AUX_WORD_1 (*(volatile mg_sdk_u16 *)0x0398UL)
#define RELAUNCH_COOKIE_0 (*(volatile mg_sdk_u16 *)0x60f0UL)
#define RELAUNCH_COOKIE_1 (*(volatile mg_sdk_u16 *)0x60f1UL)

enum {
    RELAUNCH_COOKIE_MAGIC_0 = 0x5344,
    RELAUNCH_COOKIE_MAGIC_1 = 0x4b54
};

enum {
    ST_MODE = 0,
    ST_SELECTED,
    ST_COMPLETED,
    ST_FAILED,
    ST_TEXT_COUNT,
    ST_SUBPHASE,
    ST_FRAMES,
    ST_FLAGS,
    ST_HANDLE_LO,
    ST_HANDLE_HI,
    ST_BACKGROUND_LO,
    ST_BACKGROUND_HI,
    ST_SETTINGS_LO,
    ST_SETTINGS_HI,
    ST_POWEROFF_LO,
    ST_POWEROFF_HI,
    ST_ANIMATION_LO,
    ST_ANIMATION_HI,
    ST_FONT_SLOT,
    ST_ANIMATION_SLOT,
    ST_ORIGINAL_VOLUME,
    ST_ORIGINAL_BRIGHTNESS,
    ST_TOUCH_X,
    ST_TOUCH_Y,
    ST_LAST_CODE,
    ST_SELF_FAILURES,
    ST_STATUS,
    ST_SCREEN_PENDING,
    ST_SCREEN_0_LO,
    ST_SCREEN_0_HI,
    ST_SCREEN_1_LO,
    ST_SCREEN_1_HI,
    ST_SCREEN_2_LO,
    ST_SCREEN_2_HI,
    ST_SCREEN_3_LO,
    ST_SCREEN_3_HI
};

enum {
    MODE_MENU = 0,
    MODE_RESULT,
    MODE_GRAPHICS,
    MODE_GAME_KEYS,
    MODE_KEYBOARD,
    MODE_TOUCH,
    MODE_SYSTEM_KEYS,
    MODE_EFFECTS,
    MODE_MUSIC,
    MODE_RELAUNCH,
    MODE_POWEROFF,
    MODE_POWEROFF_WAIT
};

enum {
    TEST_SELF = 0,
    TEST_GRAPHICS,
    TEST_GAME_KEYS,
    TEST_KEYBOARD,
    TEST_TOUCH,
    TEST_SYSTEM_KEYS,
    TEST_STORAGE,
    TEST_EFFECTS,
    TEST_MUSIC,
    TEST_RELAUNCH,
    TEST_POWEROFF,
    TEST_COUNT
};

enum {
    PCM_WORDS = 128,
    PCM_REGION_WORDS = 130,
    PCM_0_OFFSET = 0,
    PCM_1_OFFSET = PCM_0_OFFSET + PCM_REGION_WORDS,
    ADPCM_OFFSET = PCM_1_OFFSET + PCM_REGION_WORDS,
    ADPCM_FRAMES = 8,
    ADPCM_STREAM_WORDS =
        ADPCM_FRAMES * MG_SDK_ADPCM36_FRAME_WORDS + MG_SDK_ADPCM36_END_WORDS,
    MUSIC_WAVE_OFFSET = ADPCM_OFFSET + ADPCM_STREAM_WORDS,
    MUSIC_WAVE_WORDS = 130,
    MUSIC_ENVELOPE_OFFSET = MUSIC_WAVE_OFFSET + MUSIC_WAVE_WORDS,
    AUDIO_TOTAL_WORDS = MUSIC_ENVELOPE_OFFSET + 2
};

static const char storage_path[] = "A:DEGER\\MBASORT.LST";
/* Target-side storage currently has no verified directory-enumeration API.
 * Self-relaunch therefore probes only the filenames evidenced by the bundled
 * German and US fixtures. Host NAND/USB tools perform true suffix discovery;
 * this diagnostic fallback is deliberately narrower. */
static const char known_german_self_path_noroot[] =
    "A:BUNDLE\\SY\\135800SY.MBA";
static const char known_german_self_path[] =
    "A:\\BUNDLE\\SY\\135800SY.MBA";
static const char known_us_self_path_noroot[] =
    "A:BUNDLE\\SY\\135804SY.MBA";
static const char known_us_self_path[] =
    "A:\\BUNDLE\\SY\\135804SY.MBA";

static mg_sdk_u32 state_handle(mg_sdk_u16 low_index)
{
    return (mg_sdk_u32)STATE[low_index] |
        ((mg_sdk_u32)STATE[low_index + 1] << 16);
}

static void set_state_handle(mg_sdk_u16 low_index, mg_sdk_u32 handle)
{
    STATE[low_index] = (mg_sdk_u16)handle;
    STATE[low_index + 1] = (mg_sdk_u16)(handle >> 16);
}

static const char *test_name(mg_sdk_u16 test)
{
    switch (test) {
    case TEST_SELF: return "01 PURE SDK SELF TEST";
    case TEST_GRAPHICS: return "02 GRAPHICS AND OBJECTS";
    case TEST_GAME_KEYS: return "03 ALL GAME CONTROLS";
    case TEST_KEYBOARD: return "04 KEYBOARD EVENT QUEUE";
    case TEST_TOUCH: return "05 TOUCH SCREEN QUEUE";
    case TEST_SYSTEM_KEYS: return "06 VOLUME BRIGHTNESS";
    case TEST_STORAGE: return "07 SAFE STORAGE READ";
    case TEST_EFFECTS: return "08 PCM S AND ADPCM";
    case TEST_MUSIC: return "09 MUSIC CONTROLS AUX";
    case TEST_RELAUNCH: return "10 APPLICATION RELAUNCH";
    default: return "11 POWER OFF REQUEST";
    }
}

static const char *game_key_name(mg_sdk_u16 index)
{
    switch (index) {
    case 0: return "PRESS AND RELEASE UP";
    case 1: return "PRESS AND RELEASE DOWN";
    case 2: return "PRESS AND RELEASE LEFT";
    case 3: return "PRESS AND RELEASE RIGHT";
    case 4: return "PRESS AND RELEASE ENTER";
    case 5: return "PRESS AND RELEASE EXIT";
    default: return "PRESS AND RELEASE HELP";
    }
}

static mg_sdk_u16 game_key_mask(mg_sdk_u16 index)
{
    switch (index) {
    case 0: return MG_SDK_GAME_KEY_UP;
    case 1: return MG_SDK_GAME_KEY_DOWN;
    case 2: return MG_SDK_GAME_KEY_LEFT;
    case 3: return MG_SDK_GAME_KEY_RIGHT;
    case 4: return MG_SDK_GAME_KEY_PRIMARY;
    case 5: return MG_SDK_GAME_KEY_EXIT;
    default: return MG_SDK_GAME_KEY_HELP;
    }
}

static const char *system_key_name(mg_sdk_u16 index)
{
    if (index == 0) return "PRESS RELEASE VOLUME UP";
    if (index == 1) return "PRESS RELEASE VOLUME DOWN";
    return "PRESS RELEASE BRIGHTNESS";
}

static mg_sdk_u16 system_key_mask(mg_sdk_u16 index)
{
    if (index == 0) return MG_SDK_KEY_VOLUME_UP;
    if (index == 1) return MG_SDK_KEY_VOLUME_DOWN;
    return MG_SDK_KEY_BRIGHTNESS;
}

static void clear_text(void)
{
    if (STATE[ST_TEXT_COUNT] != 0 && STATE[ST_TEXT_COUNT] != 0xffff) {
        mobigo_clean_font_destroy_text(TEXT_HANDLES, STATE[ST_TEXT_COUNT]);
    }
    STATE[ST_TEXT_COUNT] = 0;
}

static void cleanup_title_objects(void)
{
    clear_text();
    if (state_handle(ST_BACKGROUND_LO) != MG_SDK_INVALID_UI_HANDLE &&
        state_handle(ST_BACKGROUND_LO) != 0) {
        mg_sdk_ui_a_destroy(state_handle(ST_BACKGROUND_LO));
        set_state_handle(ST_BACKGROUND_LO, MG_SDK_INVALID_UI_HANDLE);
    }
    if (state_handle(ST_SETTINGS_LO) != MG_SDK_INVALID_UI_HANDLE &&
        state_handle(ST_SETTINGS_LO) != 0) {
        mg_sdk_ui_b_destroy(state_handle(ST_SETTINGS_LO));
        set_state_handle(ST_SETTINGS_LO, MG_SDK_INVALID_UI_HANDLE);
    }
    if (state_handle(ST_POWEROFF_LO) != MG_SDK_INVALID_UI_HANDLE &&
        state_handle(ST_POWEROFF_LO) != 0) {
        mg_sdk_ui_b_destroy(state_handle(ST_POWEROFF_LO));
        set_state_handle(ST_POWEROFF_LO, MG_SDK_INVALID_UI_HANDLE);
    }
    if (state_handle(ST_ANIMATION_LO) != MG_SDK_INVALID_UI_HANDLE &&
        state_handle(ST_ANIMATION_LO) != 0) {
        mg_sdk_ui_b_destroy(state_handle(ST_ANIMATION_LO));
        set_state_handle(ST_ANIMATION_LO, MG_SDK_INVALID_UI_HANDLE);
    }
}

static void add_text_line(const char *text, mg_sdk_u16 y)
{
    mg_sdk_u16 count;
    mg_sdk_u16 used = STATE[ST_TEXT_COUNT];
    if (used >= 56) return;
    count = mobigo_clean_font_create_text(
        STATE[ST_FONT_SLOT], text, 8, y,
        TEXT_HANDLES + used, (mg_sdk_u16)(56 - used));
    if (count == 0xffff) {
        STATE[ST_STATUS] = 0xef01;
        return;
    }
    STATE[ST_TEXT_COUNT] = (mg_sdk_u16)(used + count);
}

static void store_screen_pointer(mg_sdk_u16 low_index, const char *text)
{
    mg_sdk_u32 value = (mg_sdk_u32)text;
    STATE[low_index] = (mg_sdk_u16)value;
    STATE[low_index + 1] = (mg_sdk_u16)(value >> 16);
}

static const char *load_screen_pointer(mg_sdk_u16 low_index)
{
    return (const char *)state_handle(low_index);
}

static void show_screen(
    const char *line_0, const char *line_1,
    const char *line_2, const char *line_3)
{
    clear_text();
    if (state_handle(ST_BACKGROUND_LO) != MG_SDK_INVALID_UI_HANDLE &&
        state_handle(ST_BACKGROUND_LO) != 0) {
        mg_sdk_ui_a_destroy(state_handle(ST_BACKGROUND_LO));
    }
    set_state_handle(
        ST_BACKGROUND_LO, hw_primary_create_background());
    store_screen_pointer(ST_SCREEN_0_LO, line_0);
    store_screen_pointer(ST_SCREEN_1_LO, line_1);
    store_screen_pointer(ST_SCREEN_2_LO, line_2);
    store_screen_pointer(ST_SCREEN_3_LO, line_3);
    STATE[ST_SCREEN_PENDING] = 2;
}

static int update_screen_transition(void)
{
    if (STATE[ST_SCREEN_PENDING] == 0) return 0;
    if (STATE[ST_SCREEN_PENDING] > 1) {
        STATE[ST_SCREEN_PENDING]--;
        return 1;
    }
    if (state_handle(ST_BACKGROUND_LO) != MG_SDK_INVALID_UI_HANDLE &&
        state_handle(ST_BACKGROUND_LO) != 0) {
        mg_sdk_ui_a_destroy(state_handle(ST_BACKGROUND_LO));
    }
    set_state_handle(ST_BACKGROUND_LO, MG_SDK_INVALID_UI_HANDLE);
    if (load_screen_pointer(ST_SCREEN_0_LO) != 0)
        add_text_line(load_screen_pointer(ST_SCREEN_0_LO), 42);
    if (load_screen_pointer(ST_SCREEN_1_LO) != 0)
        add_text_line(load_screen_pointer(ST_SCREEN_1_LO), 76);
    if (load_screen_pointer(ST_SCREEN_2_LO) != 0)
        add_text_line(load_screen_pointer(ST_SCREEN_2_LO), 110);
    if (load_screen_pointer(ST_SCREEN_3_LO) != 0)
        add_text_line(load_screen_pointer(ST_SCREEN_3_LO), 144);
    STATE[ST_SCREEN_PENDING] = 0;
    return 1;
}

static void show_menu(void)
{
    STATE[ST_MODE] = MODE_MENU;
    STATE[ST_SUBPHASE] = 0;
    STATE[ST_FRAMES] = 0;
    hw_primary_hide_settings(
        state_handle(ST_SETTINGS_LO));
    mg_sdk_ui_b_object_hide((struct mg_sdk_ui_b_object *)
        mg_sdk_ui_b_get(state_handle(ST_POWEROFF_LO)));
    show_screen(
        test_name(STATE[ST_SELECTED]),
        "UP DOWN SELECT", "ENTER RUN HELP", 0);
}

static void show_result(mg_sdk_u16 test, int passed, const char *detail)
{
    mg_sdk_u16 bit = (mg_sdk_u16)(1U << test);
    STATE[ST_COMPLETED] |= bit;
    if (passed) STATE[ST_FAILED] &= (mg_sdk_u16)~bit;
    else STATE[ST_FAILED] |= bit;
    STATE[ST_MODE] = MODE_RESULT;
    show_screen(
        passed ? "PASS" : "FAIL",
        detail, "ENTER OR EXIT MENU", 0);
}

static const char *find_known_self_path(void)
{
    if (mg_sdk_resident_path_exists(known_german_self_path_noroot))
        return known_german_self_path_noroot;
    if (mg_sdk_resident_path_exists(known_german_self_path))
        return known_german_self_path;
    if (mg_sdk_resident_path_exists(known_us_self_path_noroot))
        return known_us_self_path_noroot;
    if (mg_sdk_resident_path_exists(known_us_self_path))
        return known_us_self_path;
    return 0;
}

static int run_storage_test(void)
{
    mg_sdk_file_handle file;
    mg_sdk_u32 amount;
    mg_sdk_u32 size;
    mg_sdk_u32 read_size;
    mg_sdk_u16 words;
    mg_sdk_u16 index;
    int ok = 1;

    /*
     * Use an existing, small system list and never open it writable. Physical
     * testing showed that relying on publication of a newly created pathname
     * is not safe enough for the diagnostic suite. Write/truncate/remove stay
     * covered by disposable-NAND regression tests.
     */
    if (mg_sdk_resident_storage_path_exists(storage_path) !=
        MG_SDK_STORAGE_PATH_FILE) return 0;
    file = mg_sdk_resident_file_open(storage_path, MG_SDK_FILE_OPEN_READ);
    if (file == MG_SDK_INVALID_FILE_HANDLE) return 0;
    size = mg_sdk_resident_file_size(file);
    if (size == 0 || size == MG_SDK_FILE_IO_ERROR) {
        mg_sdk_resident_file_close(file);
        return 0;
    }
    read_size = size < 8 ? size : 8;
    amount = mg_sdk_resident_file_read(IO_BUFFER, read_size, file);
    ok &= amount == read_size;
    words = (mg_sdk_u16)((read_size + 1) / 2);
    for (index = 0; index < words; index++)
        IO_BUFFER[8 + index] = IO_BUFFER[index];
    ok &= mg_sdk_resident_file_seek_absolute(file, 0) == 0;
    for (index = 0; index < words; index++) IO_BUFFER[index] = 0;
    amount = mg_sdk_resident_file_read(IO_BUFFER, read_size, file);
    ok &= amount == read_size;
    for (index = 0; index < words; index++)
        ok &= IO_BUFFER[index] == IO_BUFFER[8 + index];
    ok &= mg_sdk_resident_file_close(file) == 0;
    return ok;
}

static void prepare_audio(void)
{
    mg_sdk_u32 resources[6];
    mg_sdk_u16 children[2];
    mg_sdk_s16 samples[MG_SDK_ADPCM36_SAMPLES_PER_FRAME];
    struct mg_sdk_audio_m_stream_writer writer;
    mg_sdk_u16 aux_a[2];
    mg_sdk_u16 aux_b[2];
    mg_sdk_u16 index;
    mg_sdk_u16 frame;

    for (index = 0; index < PCM_WORDS; index++) {
        AUDIO_WAVES[PCM_0_OFFSET + index] =
            (index & 2) ? 0xc0c0 : 0x4040;
        AUDIO_WAVES[PCM_1_OFFSET + index] =
            (index & 4) ? 0xd0d0 : 0x3030;
        AUDIO_WAVES[MUSIC_WAVE_OFFSET + index] =
            (mg_sdk_u16)((index << 8) | (255 - index));
    }
    AUDIO_WAVES[PCM_0_OFFSET + PCM_WORDS] = 0xffff;
    AUDIO_WAVES[PCM_0_OFFSET + PCM_WORDS + 1] = 0;
    AUDIO_WAVES[PCM_1_OFFSET + PCM_WORDS] = 0xffff;
    AUDIO_WAVES[PCM_1_OFFSET + PCM_WORDS + 1] = 0;
    AUDIO_WAVES[MUSIC_WAVE_OFFSET + PCM_WORDS] = 0xffff;
    AUDIO_WAVES[MUSIC_WAVE_OFFSET + PCM_WORDS + 1] = 0;
    mg_sdk_audio_prepare_hold_envelope(
        AUDIO_WAVES + MUSIC_ENVELOPE_OFFSET, 0x20);

    for (index = 0; index < MG_SDK_ADPCM36_SAMPLES_PER_FRAME; index++) {
        samples[index] = (index & 4) ? -12288 : 12288;
    }
    for (frame = 0; frame < ADPCM_FRAMES; frame++) {
        mg_sdk_adpcm36_encode_frame(
            AUDIO_WAVES + ADPCM_OFFSET +
                frame * MG_SDK_ADPCM36_FRAME_WORDS,
            samples);
    }
    mg_sdk_adpcm36_finish(
        AUDIO_WAVES + ADPCM_OFFSET +
            ADPCM_FRAMES * MG_SDK_ADPCM36_FRAME_WORDS);

    resources[0] = 0x00006220UL;
    resources[1] = 0x00006240UL;
    resources[2] = 0x00006260UL;
    resources[3] = 0x00006280UL;
    resources[4] = 0x000062a0UL;
    resources[5] = 0x000062c0UL;
    mg_sdk_audio_prepare_root(
        AUDIO_ROOT, 2, 3, 1, resources, 0x000062e0UL);

    mg_sdk_audio_m_writer_init(
        &writer, MUSIC_RECORD + MG_SDK_AUDIO_M_WORD_STREAM, 18);
    mg_sdk_audio_m_write_marker(&writer, 120);
    mg_sdk_audio_m_write_program_change(&writer, 0, 0);
    mg_sdk_audio_m_write_control_change(&writer, 0, 7, 100);
    mg_sdk_audio_m_write_note(&writer, 0, 60, 100, 16);
    mg_sdk_audio_m_write_wait(&writer, 24);
    mg_sdk_audio_m_write_end(&writer);
    mg_sdk_audio_prepare_m_header(MUSIC_RECORD, writer.count);

    aux_a[0] = 0x1234; aux_a[1] = 0x5678;
    aux_b[0] = 0x9abc; aux_b[1] = 0xdef0;
    mg_sdk_audio_m_writer_init(
        &writer, AUX_RECORD + MG_SDK_AUDIO_M_WORD_STREAM, 20);
    mg_sdk_audio_m_write_skip_word(&writer, 0xabcd);
    mg_sdk_audio_m_write_aux_cb(&writer, 3, 0x4567, aux_a, 2);
    mg_sdk_audio_m_write_aux(&writer, aux_b, 2);
    mg_sdk_audio_m_write_wait(&writer, 2);
    mg_sdk_audio_m_write_end(&writer);
    mg_sdk_audio_prepare_m_header(AUX_RECORD, writer.count);

    mg_sdk_audio_prepare_w_pcm8(
        W_RECORD_0, PCM_REGION_WORDS * 2, 4000, PCM_WORDS * 2,
        PCM_0_OFFSET * 2);
    mg_sdk_audio_prepare_w_pcm8(
        W_RECORD_1, PCM_REGION_WORDS * 2, 6000, PCM_WORDS * 2,
        PCM_1_OFFSET * 2);
    mg_sdk_audio_prepare_w_adpcm36(
        W_RECORD_ADPCM, ADPCM_STREAM_WORDS * 2, 4000,
        ADPCM_FRAMES * MG_SDK_ADPCM36_SAMPLES_PER_FRAME,
        ADPCM_OFFSET * 2);
    children[0] = 5; children[1] = 6;
    mg_sdk_audio_prepare_s_sequence(S_RECORD, children, 2);
    mg_sdk_audio_prepare_wave_layout(
        AUDIO_LAYOUT, (mg_sdk_u32)AUDIO_WAVES, AUDIO_TOTAL_WORDS);
    mg_sdk_audio_prepare_single_pcm8_patch_root(
        PATCH_ROOT, 0x000062e0UL, 0, 60, 127, 8000,
        MUSIC_WAVE_OFFSET * 2, MUSIC_WAVE_OFFSET,
        MUSIC_ENVELOPE_OFFSET);
    mg_sdk_resident_register_audio_resources(AUDIO_ROOT, PATCH_ROOT);
}

static void touch_callback(void *user, const struct mg_sdk_touch_event *event)
{
    (void)user;
    if (event->state == MG_SDK_TOUCH_STATE_COORDINATE) {
        STATE[ST_FLAGS] |= 1;
        STATE[ST_TOUCH_X] = (mg_sdk_u16)event->x;
        STATE[ST_TOUCH_Y] = (mg_sdk_u16)event->y;
    } else if (event->state == MG_SDK_TOUCH_STATE_SENTINEL) {
        STATE[ST_FLAGS] |= 2;
    }
}

static void begin_test(mg_sdk_u16 test)
{
    mg_sdk_u16 value;
    STATE[ST_SUBPHASE] = 0;
    STATE[ST_FRAMES] = 0;
    STATE[ST_FLAGS] = 0;

    if (test == TEST_SELF) {
        value = hardware_run_pure_self_tests();
        STATE[ST_SELF_FAILURES] = value;
        show_result(TEST_SELF, value == 0,
            value == 0 ? "ALL PORTABLE HELPERS" : "ONE OR MORE CHECKS FAILED");
    } else if (test == TEST_GRAPHICS) {
        STATE[ST_MODE] = MODE_GRAPHICS;
        show_screen("GRAPHICS STEP ONE", "ENTER SHOWS BACKGROUND",
            "THEN ENTER CONFIRMS", 0);
    } else if (test == TEST_GAME_KEYS) {
        STATE[ST_MODE] = MODE_GAME_KEYS;
        show_screen("GAME CONTROLS", game_key_name(0),
            "PRESS THEN RELEASE", 0);
    } else if (test == TEST_KEYBOARD) {
        STATE[ST_MODE] = MODE_KEYBOARD;
        show_screen("KEYBOARD QUEUE", "PRESS ANY LETTER KEY",
            "EXIT CANCELS", 0);
    } else if (test == TEST_TOUCH) {
        STATE[ST_MODE] = MODE_TOUCH;
        show_screen("TOUCH QUEUE", "TAP THEN RELEASE SCREEN",
            "EXIT CANCELS", 0);
    } else if (test == TEST_SYSTEM_KEYS) {
        STATE[ST_MODE] = MODE_SYSTEM_KEYS;
        mg_sdk_system_controls_init(
            SYSTEM_CONTROLS, &mg_sdk_experimental_resident_backend, 0);
        STATE[ST_ORIGINAL_VOLUME] = SYSTEM_CONTROLS->volume;
        STATE[ST_ORIGINAL_BRIGHTNESS] = SYSTEM_CONTROLS->brightness;
        value = (mg_sdk_u16)((SYSTEM_CONTROLS->volume + 1) %
            MG_SDK_VOLUME_LEVELS);
        mg_sdk_volume_set(SYSTEM_CONTROLS, value, 0);
        mg_sdk_volume_set(
            SYSTEM_CONTROLS, STATE[ST_ORIGINAL_VOLUME], 0);
        value = (mg_sdk_u16)((SYSTEM_CONTROLS->brightness + 1) %
            MG_SDK_BRIGHTNESS_LEVELS);
        mg_sdk_brightness_set(SYSTEM_CONTROLS, value, 0);
        mg_sdk_brightness_set(
            SYSTEM_CONTROLS, STATE[ST_ORIGINAL_BRIGHTNESS], 0);
        show_screen("SYSTEM CONTROLS", system_key_name(0),
            "OFF TEST IS LAST", 0);
    } else if (test == TEST_STORAGE) {
        show_result(TEST_STORAGE, run_storage_test(),
            "PATH OPEN SIZE READ SEEK CLOSE");
    } else if (test == TEST_EFFECTS) {
        STATE[ST_MODE] = MODE_EFFECTS;
        show_screen("AUDIO EFFECTS", "PCM SEQUENCE ADPCM36",
            "LISTEN OR EXIT", 0);
    } else if (test == TEST_MUSIC) {
        STATE[ST_MODE] = MODE_MUSIC;
        show_screen("MUSIC ENGINE", "NOTE PAUSE LEVEL AUX",
            "LISTEN OR EXIT", 0);
    } else if (test == TEST_RELAUNCH) {
        STATE[ST_MODE] = MODE_RELAUNCH;
        show_screen("SELF RELAUNCH", "REQUIRES SY SYSTEM SLOT",
            "ENTER RESTART EXIT CANCEL", 0);
    } else {
        STATE[ST_MODE] = MODE_POWEROFF;
        hw_primary_show_poweroff(
            state_handle(ST_POWEROFF_LO));
        show_screen("POWER OFF FINAL", "ENTER REQUESTS SHUTDOWN",
            "SHUTDOWN ITSELF IS PASS", 0);
    }
}

static void poll_graphics(void)
{
    struct mg_sdk_ui_b_object *object = (struct mg_sdk_ui_b_object *)
        mg_sdk_ui_b_get(state_handle(ST_ANIMATION_LO));
    STATE[ST_FRAMES]++;
    if (STATE[ST_SUBPHASE] == 2 && object != 0 &&
        object->word[MG_SDK_UI_B_OBJECT_WORD_RECORD] == 1) {
        STATE[ST_FLAGS] |= 1;
    }
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_EXIT)) {
        show_result(TEST_GRAPHICS, 0, "USER REPORTED VISUAL FAILURE");
    } else if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_PRIMARY)) {
        if (STATE[ST_SUBPHASE] == 0) {
            set_state_handle(
                ST_BACKGROUND_LO, hw_primary_create_background());
            if (state_handle(ST_BACKGROUND_LO) == MG_SDK_INVALID_UI_HANDLE ||
                mg_sdk_ui_a_get(state_handle(ST_BACKGROUND_LO)) == 0) {
                show_result(TEST_GRAPHICS, 0, "FAMILY A CREATE FAILED");
            } else {
                clear_text();
                STATE[ST_SUBPHASE] = 1;
            }
        } else if (STATE[ST_SUBPHASE] == 1) {
            mg_sdk_ui_a_destroy(state_handle(ST_BACKGROUND_LO));
            set_state_handle(ST_BACKGROUND_LO, MG_SDK_INVALID_UI_HANDLE);
            hw_primary_show_brightness(state_handle(ST_SETTINGS_LO), 3);
            hw_primary_show_poweroff(state_handle(ST_POWEROFF_LO));
            if (object != 0) {
                mg_sdk_ui_b_object_play_animation(
                    object, 0, 0, 220, 110, 1);
            }
            STATE[ST_SUBPHASE] = 2;
            STATE[ST_FRAMES] = 0;
            show_screen("GRAPHICS STEP TWO", "TEXT ICONS AND MOTION",
                "ENTER PASS EXIT FAIL", 0);
        } else {
            show_result(TEST_GRAPHICS,
                object != 0 && (STATE[ST_FLAGS] & 1) != 0,
                "FAMILY A FAMILY B ANIMATION");
        }
    }
}

static void poll_game_keys(void)
{
    mg_sdk_u16 index = STATE[ST_FLAGS];
    mg_sdk_u16 mask = game_key_mask(index);
    if (STATE[ST_SUBPHASE] == 0) {
        if (!mg_sdk_resident_game_key_down(mask)) STATE[ST_SUBPHASE] = 1;
    } else if (STATE[ST_SUBPHASE] == 1) {
        if (mg_sdk_resident_game_key_pressed(mask) &&
            mg_sdk_resident_game_key_down(mask)) STATE[ST_SUBPHASE] = 2;
    } else if (mg_sdk_resident_game_key_released(mask) &&
               !mg_sdk_resident_game_key_down(mask)) {
        index++;
        STATE[ST_FLAGS] = index;
        STATE[ST_SUBPHASE] = 0;
        if (index == 7) {
            show_result(TEST_GAME_KEYS, 1, "ALL SEVEN GAME CONTROLS");
        } else {
            show_screen("GAME CONTROLS", game_key_name(index),
                "PRESS THEN RELEASE", 0);
        }
    }
}

static void poll_keyboard(void)
{
    mg_sdk_u16 code;
    struct mg_sdk_input_pump pump;
    STATE[ST_FRAMES]++;
    if (STATE[ST_FRAMES] > 8 &&
        mg_sdk_experimental_resident_input_backend.first_buffered_code(
            0, &code)) {
        STATE[ST_LAST_CODE] = code;
        mg_sdk_input_init(
            &pump, &mg_sdk_experimental_resident_input_backend, 0);
        mg_sdk_input_poll(&pump);
        show_result(TEST_KEYBOARD, 1, "BUFFER AND FRAMEWORK PUMP");
    } else if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_EXIT)) {
        show_result(TEST_KEYBOARD, 0, "NO KEYBOARD EVENT OBSERVED");
    }
}

static void poll_touch(void)
{
    mg_sdk_touch_poll(
        &mg_sdk_experimental_resident_touch_backend, 0,
        touch_callback, 0);
    if ((STATE[ST_FLAGS] & 3) == 3) {
        show_result(TEST_TOUCH, 1, "COORDINATE AND RELEASE SENTINEL");
    } else if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_EXIT)) {
        show_result(TEST_TOUCH, 0, "TOUCH QUEUE INCOMPLETE");
    }
}

static void poll_system_keys(void)
{
    mg_sdk_u16 index = STATE[ST_FLAGS];
    mg_sdk_u16 mask = system_key_mask(index);
    mg_sdk_u16 level;
    if (STATE[ST_SUBPHASE] == 0) {
        if (!mg_sdk_resident_system_key_down(mask)) STATE[ST_SUBPHASE] = 1;
    } else if (STATE[ST_SUBPHASE] == 1) {
        if (mg_sdk_resident_system_key_pressed(mask) &&
            mg_sdk_resident_system_key_down(mask)) {
            STATE[ST_SUBPHASE] = 2;
            if (index < 2) {
                mg_sdk_experimental_resident_backend.load_volume(0, &level);
                hw_primary_show_volume(
                    state_handle(ST_SETTINGS_LO), level);
            } else {
                mg_sdk_experimental_resident_backend.load_brightness(0, &level);
                hw_primary_show_brightness(
                    state_handle(ST_SETTINGS_LO), level);
            }
        }
    } else if (mg_sdk_resident_system_key_released(mask) &&
               !mg_sdk_resident_system_key_down(mask)) {
        index++;
        STATE[ST_FLAGS] = index;
        STATE[ST_SUBPHASE] = 0;
        if (index == 3) {
            mg_sdk_volume_set(
                SYSTEM_CONTROLS, STATE[ST_ORIGINAL_VOLUME], 0);
            mg_sdk_brightness_set(
                SYSTEM_CONTROLS, STATE[ST_ORIGINAL_BRIGHTNESS], 0);
            show_result(TEST_SYSTEM_KEYS, 1,
                "KEY EDGES LEVELS HARDWARE APPLY");
        } else {
            show_screen("SYSTEM CONTROLS", system_key_name(index),
                "OFF TEST IS LAST", 0);
        }
    }
}

static int sound_stopped(void)
{
    mg_sdk_u16 value = 0xffff;
    mg_sdk_resident_get_sound_state(state_handle(ST_HANDLE_LO), &value);
    STATE[ST_LAST_CODE] = value;
    if (value == MG_SDK_SOUND_STATE_PLAYING) {
        /* A fixed upper bound keeps the listening test moving if a hardware
         * revision leaves a stale playing state after the short sample. */
        return STATE[ST_FRAMES] >= 60;
    }
    if (value != 0xffff) return 1;
    return STATE[ST_FRAMES] >= 60;
}

static void poll_effects(void)
{
    mg_sdk_u32 handle;
    STATE[ST_FRAMES]++;
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_EXIT)) {
        show_result(TEST_EFFECTS, 0, "USER CANCELLED AUDIO TEST");
        return;
    }
    if (STATE[ST_SUBPHASE] == 0) {
        handle = mg_sdk_resident_play_sound(5, 0x7f, 0x30, 0, 0);
        set_state_handle(ST_HANDLE_LO, handle);
        STATE[ST_FLAGS] = (mg_sdk_u16)(handle != 0xffffffffUL);
        STATE[ST_SUBPHASE] = 1; STATE[ST_FRAMES] = 0;
    } else if (STATE[ST_SUBPHASE] == 1 &&
               STATE[ST_FRAMES] > 2 && sound_stopped()) {
        handle = mg_sdk_resident_play_sound(8, 0x7f, 0x40, 0, 0);
        set_state_handle(ST_HANDLE_LO, handle);
        STATE[ST_FLAGS] &= (mg_sdk_u16)(handle != 0xffffffffUL);
        STATE[ST_SUBPHASE] = 2; STATE[ST_FRAMES] = 0;
    } else if (STATE[ST_SUBPHASE] == 2 &&
               STATE[ST_FRAMES] > 2 && sound_stopped()) {
        handle = mg_sdk_resident_play_sound(7, 0x7f, 0x50, 0, 0);
        set_state_handle(ST_HANDLE_LO, handle);
        STATE[ST_FLAGS] &= (mg_sdk_u16)(handle != 0xffffffffUL);
        STATE[ST_SUBPHASE] = 3; STATE[ST_FRAMES] = 0;
    } else if (STATE[ST_SUBPHASE] == 3 &&
               STATE[ST_FRAMES] > 2 && sound_stopped()) {
        show_result(TEST_EFFECTS, STATE[ST_FLAGS] != 0,
            "PCM S ADPCM36 STATE QUERIES");
    } else if (STATE[ST_FRAMES] > 240) {
        show_result(TEST_EFFECTS, 0, "AUDIO STATE TIMEOUT");
    }
}

static void poll_music(void)
{
    mg_sdk_u32 handle;
    mg_sdk_u16 state = 0xffff;
    mg_sdk_u16 level = 0;
    STATE[ST_FRAMES]++;
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_EXIT)) {
        if (STATE[ST_SUBPHASE] != 0)
            mg_sdk_resident_stop_music(state_handle(ST_HANDLE_LO));
        show_result(TEST_MUSIC, 0, "USER CANCELLED MUSIC TEST");
        return;
    }
    if (STATE[ST_SUBPHASE] == 0) {
        handle = mg_sdk_resident_play_music(3, 0x60, 1, 3);
        set_state_handle(ST_HANDLE_LO, handle);
        if (handle == 0xffffffffUL) {
            show_result(TEST_MUSIC, 0, "MUSIC HANDLE FAILED");
            return;
        }
        STATE[ST_FLAGS] = 1;
        STATE[ST_SUBPHASE] = 1; STATE[ST_FRAMES] = 0;
    } else if (STATE[ST_SUBPHASE] == 1 && STATE[ST_FRAMES] >= 2) {
        handle = state_handle(ST_HANDLE_LO);
        mg_sdk_resident_get_music_state(handle, &state);
        mg_sdk_resident_set_music_level(handle, 0x40);
        mg_sdk_resident_get_music_level(handle, &level);
        if (level == 0x40) STATE[ST_FLAGS] |= 2;
        mg_sdk_resident_set_music_repeat(handle, 0);
        mg_sdk_resident_pause_music(handle);
        STATE[ST_SUBPHASE] = 2; STATE[ST_FRAMES] = 0;
    } else if (STATE[ST_SUBPHASE] == 2 && STATE[ST_FRAMES] >= 2) {
        mg_sdk_resident_get_music_state(state_handle(ST_HANDLE_LO), &state);
        if (state == 1) STATE[ST_FLAGS] |= 4;
        mg_sdk_resident_resume_music(state_handle(ST_HANDLE_LO));
        STATE[ST_SUBPHASE] = 3; STATE[ST_FRAMES] = 0;
    } else if (STATE[ST_SUBPHASE] == 3) {
        mg_sdk_resident_get_music_state(state_handle(ST_HANDLE_LO), &state);
        if (state == 2) STATE[ST_FLAGS] |= 8;
        if (STATE[ST_FRAMES] > 30) {
            mg_sdk_resident_stop_music(state_handle(ST_HANDLE_LO));
            handle = mg_sdk_resident_play_music(4, 0x40, 0, 3);
            set_state_handle(ST_HANDLE_LO, handle);
            if (handle == 0xffffffffUL) {
                show_result(TEST_MUSIC, 0, "AUX MUSIC HANDLE FAILED");
                return;
            }
            STATE[ST_SUBPHASE] = 4; STATE[ST_FRAMES] = 0;
        }
    } else if (STATE[ST_SUBPHASE] == 4) {
        mg_sdk_resident_get_music_state(state_handle(ST_HANDLE_LO), &state);
        if ((state == 0 || state == 4) && STATE[ST_FRAMES] > 2) {
            if (MUSIC_AUX_WORD_0 == 0x9abc &&
                MUSIC_AUX_WORD_1 == 0xdef0) STATE[ST_FLAGS] |= 16;
            if ((STATE[ST_FLAGS] & 2) == 0)
                show_result(TEST_MUSIC, 0, "MUSIC LEVEL GET SET FAILED");
            else if ((STATE[ST_FLAGS] & 12) != 12)
                show_result(TEST_MUSIC, 0, "PAUSE RESUME STATE FAILED");
            else if ((STATE[ST_FLAGS] & 16) == 0)
                show_result(TEST_MUSIC, 0, "AUX BLOCK RESULT FAILED");
            else
                show_result(TEST_MUSIC, 1,
                    "M NOTE CONTROLS IRQ AUX BLOCK");
        } else if (STATE[ST_FRAMES] > 120) {
            show_result(TEST_MUSIC, 0, "MUSIC OR AUX TIMEOUT");
        }
    }
}

static void poll_menu(void)
{
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_UP)) {
        if (STATE[ST_SELECTED] == 0) STATE[ST_SELECTED] = TEST_COUNT - 1;
        else STATE[ST_SELECTED]--;
        show_menu();
    } else if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_DOWN)) {
        STATE[ST_SELECTED]++;
        if (STATE[ST_SELECTED] >= TEST_COUNT) STATE[ST_SELECTED] = 0;
        show_menu();
    } else if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_PRIMARY)) {
        begin_test(STATE[ST_SELECTED]);
    } else if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_HELP)) {
        show_screen("SUITE SUMMARY", "RESULTS IN THIS SESSION",
            STATE[ST_FAILED] == 0 ? "NO RECORDED FAILURES" : "FAILURES RECORDED",
            0);
        STATE[ST_MODE] = MODE_RESULT;
    }
}

static int app_start(void) { return 1; }

static int app_frame(mg_sdk_u32 ticks)
{
    (void)ticks;
    if (update_screen_transition()) return 1;
    if (STATE[ST_MODE] == MODE_MENU) poll_menu();
    else if (STATE[ST_MODE] == MODE_RESULT) {
        if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_PRIMARY) ||
            mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_EXIT)) show_menu();
    } else if (STATE[ST_MODE] == MODE_GRAPHICS) poll_graphics();
    else if (STATE[ST_MODE] == MODE_GAME_KEYS) poll_game_keys();
    else if (STATE[ST_MODE] == MODE_KEYBOARD) poll_keyboard();
    else if (STATE[ST_MODE] == MODE_TOUCH) poll_touch();
    else if (STATE[ST_MODE] == MODE_SYSTEM_KEYS) poll_system_keys();
    else if (STATE[ST_MODE] == MODE_EFFECTS) poll_effects();
    else if (STATE[ST_MODE] == MODE_MUSIC) poll_music();
    else if (STATE[ST_MODE] == MODE_RELAUNCH) {
        if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_EXIT)) show_menu();
        else if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_PRIMARY)) {
            mg_sdk_u32 arguments[1];
            const char *path = find_known_self_path();
            arguments[0] = 999;
            if (path == 0) {
                show_result(TEST_RELAUNCH, 0, "INSTALLED SY PATH NOT FOUND");
            } else {
                RELAUNCH_COOKIE_0 = RELAUNCH_COOKIE_MAGIC_0;
                RELAUNCH_COOKIE_1 = RELAUNCH_COOKIE_MAGIC_1;
                /* Match SY's verified launch order: tear down title objects,
                 * schedule one official argument (999), then end the frame. */
                cleanup_title_objects();
                mg_sdk_resident_launch_mba(path, 1, arguments);
                return 0;
            }
        }
    } else if (STATE[ST_MODE] == MODE_POWEROFF) {
        if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_EXIT)) {
            show_menu();
        } else if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_PRIMARY)) {
            mg_sdk_experimental_resident_backend.request_poweroff(0);
            STATE[ST_MODE] = MODE_POWEROFF_WAIT;
            STATE[ST_FRAMES] = 0;
            show_screen("POWER REQUEST SENT", "WAIT FOR SHUTDOWN",
                "SHUTDOWN CONFIRMS PASS", 0);
        }
    } else if (STATE[ST_MODE] == MODE_POWEROFF_WAIT) {
        STATE[ST_FRAMES]++;
        if (STATE[ST_FRAMES] > 300) {
            show_result(TEST_POWEROFF, 0, "POWER OFF DID NOT OCCUR");
        }
    }
    return 1;
}

static void app_stop(void)
{
    cleanup_title_objects();
}

int main(void)
{
    struct mg_sdk_runtime_callbacks callbacks;
    struct mg_sdk_ui_b_object *animation_object;
    mg_sdk_ui_handle handle;
    mg_sdk_u32 scratch = 0;
    mg_sdk_u16 slot;
    mg_sdk_u16 index;
    int relaunched =
        RELAUNCH_COOKIE_0 == RELAUNCH_COOKIE_MAGIC_0 &&
        RELAUNCH_COOKIE_1 == RELAUNCH_COOKIE_MAGIC_1;

    RELAUNCH_COOKIE_0 = 0;
    RELAUNCH_COOKIE_1 = 0;
    for (index = 0; index < 64; index++) STATE[index] = 0;
    STATE[ST_STATUS] = 0x8000;
    if (mg_sdk_resident_runtime_setup(&scratch) == 0) {
        STATE[ST_STATUS] = 0xe800;
        for (;;) {}
    }

    hw_primary_copy_bundle(PRIMARY_BUNDLE_RAM);
    hw_primary_register(PRIMARY_BUNDLE_RAM);
    handle = hw_primary_create_background();
    set_state_handle(ST_BACKGROUND_LO, handle);
    handle = hw_primary_create_settings();
    set_state_handle(ST_SETTINGS_LO, handle);
    handle = hw_primary_create_poweroff();
    set_state_handle(ST_POWEROFF_LO, handle);

    mobigo_clean_font_copy_bundle(FONT_BUNDLE_RAM);
    slot = mobigo_clean_font_register_dynamic(FONT_BUNDLE_RAM);
    STATE[ST_FONT_SLOT] = slot;

    hw_animation_copy_bundle(ANIMATION_BUNDLE_RAM);
    slot = mg_sdk_resident_register_dynamic_bundle(
        ANIMATION_BUNDLE_RAM, (void *)hw_animation_primary_words);
    STATE[ST_ANIMATION_SLOT] = slot;
    handle = mg_sdk_ui_b_create_from_dynamic_bundle(
        slot, HW_ANIMATION_DESCRIPTOR);
    set_state_handle(ST_ANIMATION_LO, handle);
    animation_object = (struct mg_sdk_ui_b_object *)mg_sdk_ui_b_get(handle);
    if (animation_object != 0) mg_sdk_ui_b_object_hide(animation_object);

    if (state_handle(ST_BACKGROUND_LO) == MG_SDK_INVALID_UI_HANDLE ||
        state_handle(ST_SETTINGS_LO) == MG_SDK_INVALID_UI_HANDLE ||
        state_handle(ST_POWEROFF_LO) == MG_SDK_INVALID_UI_HANDLE ||
        state_handle(ST_ANIMATION_LO) == MG_SDK_INVALID_UI_HANDLE ||
        STATE[ST_FONT_SLOT] == 0 || STATE[ST_ANIMATION_SLOT] == 0) {
        STATE[ST_STATUS] = 0xe801;
        for (;;) {}
    }

    /* Keep menus readable. The guided graphics test creates another family-A
     * object, confirms it alone, destroys it, then validates family-B layers. */
    if (mg_sdk_ui_a_get(state_handle(ST_BACKGROUND_LO)) == 0) {
        STATE[ST_STATUS] = 0xe802;
        for (;;) {}
    }
    mg_sdk_ui_a_destroy(state_handle(ST_BACKGROUND_LO));
    set_state_handle(ST_BACKGROUND_LO, MG_SDK_INVALID_UI_HANDLE);

    prepare_audio();
    if (relaunched) {
        STATE[ST_SELECTED] = TEST_RELAUNCH;
        show_result(TEST_RELAUNCH, 1, "ASYNC SY HANDOFF RESTARTED");
    } else {
        show_menu();
    }
    STATE[ST_STATUS] = 0x8001;

    callbacks.start = app_start;
    callbacks.frame = app_frame;
    callbacks.stop = app_stop;
    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {}
    mg_sdk_resident_runtime_finalize();
    return 0;
}
