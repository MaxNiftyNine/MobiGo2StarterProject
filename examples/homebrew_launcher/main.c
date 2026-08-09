#include "mobigo_sdk/mobigo_sdk.h"
#include "mobigo_clean_font_resources.h"
#include "hb_wave_resources.h"
#include "hb_icon_resources.h"
#include "hb_music.h"

#define CONTROLS ((struct mg_sdk_direct_controls *)0x5000UL)
#define ICON_PRIMARY ((mg_sdk_u16 *)0x5040UL)
#define ICON_TEMP ((mg_sdk_u16 *)0x5740UL)
#define ICON_GRAPH ((mg_sdk_u16 *)0x57c0UL)
#define WAVE_RAM ((mg_sdk_u16 *)0x5880UL)
#define AUDIO_ROOT ((mg_sdk_u16 *)0x5a00UL)
#define AUDIO_W_RECORD ((struct mg_sdk_audio_w_record *)0x5a10UL)
#define AUDIO_LAYOUT ((mg_sdk_u16 *)0x5a30UL)
#define FONT_RAM ((mg_sdk_u16 *)0x5a40UL)
#define TEXT_HANDLES ((mg_sdk_ui_handle *)0x6350UL)
#define WAVE_HANDLES ((mg_sdk_ui_handle *)0x63c0UL)
#define ICON_HANDLES ((mg_sdk_ui_handle *)0x63e0UL)
#define STATE ((volatile mg_sdk_u16 *)0x6420UL)
#define INDEX_BUFFER ((mg_sdk_u16 *)0x6460UL)
#define LAUNCH_PATH ((char *)0x6770UL)

#define INDEX_BUFFER_BYTES 1544U
#define CATALOG_HEADER_BYTES 8U
#define CATALOG_V2_ENTRY_BYTES 96U
#define CATALOG_V1_ENTRY_BYTES 64U
#define CATALOG_PATH_BYTES 42U
#define CATALOG_TITLE_BYTES 18U
#define CATALOG_MAX_ENTRIES 16U
#define TEXT_HANDLE_CAPACITY 56U
#define WAVE_SPRITES 12U
#define CAROUSEL_SLOTS 3U
#define ICON_SOURCE_OFFSET 0x00c0UL
#define ICON_PALETTE_OFFSET 0x00a0UL
#define ICON_SOURCE_ROW_BYTES 32U
#define ICON_CHUNK_ROWS 8U

enum {
    ST_FONT_SLOT = 0,
    ST_ENTRY_COUNT,
    ST_SELECTED,
    ST_TEXT_COUNT,
    ST_STATUS,
    ST_BACKGROUND_LO,
    ST_BACKGROUND_HI,
    ST_LAUNCH_PENDING,
    ST_CATALOG_STRIDE,
    ST_TOUCH_ITEM,
    ST_TOUCH_WAS_SELECTED,
    ST_MUSIC_LO,
    ST_MUSIC_HI,
    ST_MUSIC_RESTARTS,
    ST_FRAME_COUNT,
    ST_WAVE_RECORD,
    ST_ICON_SLOT,
    ST_VISIBLE_0,
    ST_VISIBLE_1,
    ST_VISIBLE_2,
    ST_TOUCH_LAUNCHES,
    ST_ICON_REFRESHES
};

static const char catalog_path[] = "A:\\HB\\INDEX.HB";
static const char emulator_catalog_path[] = "A:DEGER\\MBASORT.LST";
static const mg_sdk_u32 launch_argument = 999UL;

static void refresh_carousel(void);
static void launch_selected(void);

static mg_sdk_u32 state_handle(mg_sdk_u16 low)
{
    return (mg_sdk_u32)STATE[low] | ((mg_sdk_u32)STATE[low + 1U] << 16);
}

static void set_state_handle(mg_sdk_u16 low, mg_sdk_u32 handle)
{
    STATE[low] = (mg_sdk_u16)handle;
    STATE[low + 1U] = (mg_sdk_u16)(handle >> 16);
}

static mg_sdk_u16 packed_byte(const mg_sdk_u16 *source, mg_sdk_u16 offset)
{
    mg_sdk_u16 value = source[offset >> 1];
    return (offset & 1U) ? (value >> 8) & 0xffU : value & 0xffU;
}

static mg_sdk_u16 catalog_byte(mg_sdk_u16 offset)
{
    return packed_byte(INDEX_BUFFER, offset);
}

static void catalog_string(
    mg_sdk_u16 offset, mg_sdk_u16 capacity, char *destination)
{
    mg_sdk_u16 index;
    mg_sdk_u16 value;
    for (index = 0; index + 1U < capacity; ++index) {
        value = catalog_byte((mg_sdk_u16)(offset + index));
        destination[index] = (char)value;
        if (value == 0U) return;
    }
    destination[capacity - 1U] = 0;
}

static mg_sdk_u16 ascii_upper(mg_sdk_u16 value)
{
    if (value >= 'a' && value <= 'z') return (mg_sdk_u16)(value - ('a' - 'A'));
    return value;
}

static int is_system_menu_path(const char *path)
{
    static const char suffix[] = "SYSTEM.MBA";
    mg_sdk_u16 length = 0;
    mg_sdk_u16 index;
    while (path[length] != 0) length++;
    if (length < 10U) return 0;
    for (index = 0; index < 10U; ++index) {
        if (ascii_upper((mg_sdk_u16)path[length - 10U + index]) !=
            (mg_sdk_u16)suffix[index]) return 0;
    }
    return 1;
}

static int is_system_menu_entry(mg_sdk_u16 entry, const char *path)
{
    static const char system_title[] = "SYSTEM MENU";
    char title[CATALOG_TITLE_BYTES];
    mg_sdk_u16 index = 0;
    if (is_system_menu_path(path)) return 1;
    catalog_string(
        (mg_sdk_u16)(CATALOG_HEADER_BYTES +
            entry * STATE[ST_CATALOG_STRIDE] + CATALOG_PATH_BYTES),
        CATALOG_TITLE_BYTES,
        title);
    while (system_title[index] != 0 && title[index] != 0) {
        if (ascii_upper((mg_sdk_u16)title[index]) !=
            (mg_sdk_u16)system_title[index]) return 0;
        index++;
    }
    return system_title[index] == 0 && title[index] == 0;
}

static int catalog_valid(mg_sdk_u32 size)
{
    mg_sdk_u16 count;
    mg_sdk_u16 stride;
    int version_two;
    if (size < CATALOG_HEADER_BYTES || size > INDEX_BUFFER_BYTES) return 0;
    if (catalog_byte(0) != 'H' || catalog_byte(1) != 'B' ||
        catalog_byte(2) != '0') return 0;
    version_two = catalog_byte(3) == '2';
    if (!version_two && catalog_byte(3) != '1') return 0;
    count = (mg_sdk_u16)(catalog_byte(4) | (catalog_byte(5) << 8));
    stride = (mg_sdk_u16)(catalog_byte(6) | (catalog_byte(7) << 8));
    if (count > CATALOG_MAX_ENTRIES) return 0;
    if ((version_two && stride != CATALOG_V2_ENTRY_BYTES) ||
        (!version_two && stride != CATALOG_V1_ENTRY_BYTES)) return 0;
    if ((mg_sdk_u32)CATALOG_HEADER_BYTES + (mg_sdk_u32)count * stride > size)
        return 0;
    STATE[ST_ENTRY_COUNT] = count;
    STATE[ST_CATALOG_STRIDE] = stride;
    return 1;
}

static int load_catalog_from(const char *path)
{
    mg_sdk_file_handle file;
    mg_sdk_u32 size;
    mg_sdk_u32 read;
    file = mg_sdk_resident_file_open(path, MG_SDK_FILE_OPEN_READ);
    if (file == MG_SDK_INVALID_FILE_HANDLE) return 0;
    size = mg_sdk_resident_file_size(file);
    if (size == 0 || size == MG_SDK_FILE_IO_ERROR || size > INDEX_BUFFER_BYTES) {
        (void)mg_sdk_resident_file_close(file);
        return 0;
    }
    read = mg_sdk_resident_file_read(INDEX_BUFFER, size, file);
    (void)mg_sdk_resident_file_close(file);
    return read == size && catalog_valid(size);
}

static mg_sdk_u16 entry_offset(mg_sdk_u16 entry)
{
    return (mg_sdk_u16)(CATALOG_HEADER_BYTES + entry * STATE[ST_CATALOG_STRIDE]);
}

static void clear_text(void)
{
    if (STATE[ST_TEXT_COUNT] != 0 && STATE[ST_TEXT_COUNT] != 0xffffU)
        mobigo_clean_font_destroy_text(TEXT_HANDLES, STATE[ST_TEXT_COUNT]);
    STATE[ST_TEXT_COUNT] = 0;
}

static void add_text(const char *text, mg_sdk_u16 x, mg_sdk_u16 y)
{
    mg_sdk_u16 used = STATE[ST_TEXT_COUNT];
    mg_sdk_u16 count;
    if (used >= TEXT_HANDLE_CAPACITY) return;
    count = mobigo_clean_font_create_text(
        STATE[ST_FONT_SLOT], text, x, y, TEXT_HANDLES + used,
        (mg_sdk_u16)(TEXT_HANDLE_CAPACITY - used));
    if (count == 0xffffU) {
        STATE[ST_STATUS] = 0xe304U;
        return;
    }
    STATE[ST_TEXT_COUNT] = (mg_sdk_u16)(used + count);
}

static mg_sdk_u16 text_length(const char *text)
{
    mg_sdk_u16 length = 0;
    while (text[length] != 0) length++;
    return length;
}

static mg_sdk_u16 visible_entry(mg_sdk_u16 slot)
{
    return STATE[(mg_sdk_u16)(ST_VISIBLE_0 + slot)];
}

static void assign_visible_entries(void)
{
    mg_sdk_u16 count = STATE[ST_ENTRY_COUNT];
    mg_sdk_u16 selected = STATE[ST_SELECTED];
    STATE[ST_VISIBLE_0] = 0xffffU;
    STATE[ST_VISIBLE_1] = 0xffffU;
    STATE[ST_VISIBLE_2] = 0xffffU;
    if (count == 0) return;
    STATE[ST_VISIBLE_1] = selected;
    if (count >= 2U) {
        STATE[ST_VISIBLE_0] = selected == 0 ? (mg_sdk_u16)(count - 1U)
            : (mg_sdk_u16)(selected - 1U);
    }
    if (count >= 3U) {
        STATE[ST_VISIBLE_2] = (mg_sdk_u16)(selected + 1U);
        if (STATE[ST_VISIBLE_2] >= count) STATE[ST_VISIBLE_2] = 0;
    }
}

static void clear_icon_pixels(mg_sdk_u16 slot)
{
    mg_sdk_u16 index;
    mg_sdk_u16 base = (mg_sdk_u16)(HB_ICON_PALETTE_WORDS +
        slot * HB_ICON_ICON_WORDS);
    for (index = 0; index < HB_ICON_ICON_WORDS; ++index)
        ICON_PRIMARY[base + index] = 0;
}

static mg_sdk_u16 channel_distance(mg_sdk_u16 left, mg_sdk_u16 right)
{
    return left >= right ? (mg_sdk_u16)(left - right)
        : (mg_sdk_u16)(right - left);
}

static mg_sdk_u16 icon_color(mg_sdk_u16 color)
{
    mg_sdk_u16 red;
    mg_sdk_u16 green;
    mg_sdk_u16 blue;
    mg_sdk_u16 dark;
    mg_sdk_u16 white;
    mg_sdk_u16 cyan;
    if (color & 0x8000U) return 0;
    red = (color >> 10) & 31U;
    green = (color >> 5) & 31U;
    blue = color & 31U;
    dark = channel_distance(red, 3U) + channel_distance(green, 8U) +
        channel_distance(blue, 15U);
    white = channel_distance(red, 29U) + channel_distance(green, 31U) +
        channel_distance(blue, 31U);
    cyan = channel_distance(red, 5U) + channel_distance(green, 22U) +
        channel_distance(blue, 31U);
    if (dark <= white && dark <= cyan) return 1;
    return white <= cyan ? 2U : 3U;
}

static int load_mba_icon(mg_sdk_u16 entry, mg_sdk_u16 slot)
{
    char path[CATALOG_PATH_BYTES];
    mg_sdk_file_handle file;
    mg_sdk_u16 chunk;
    mg_sdk_u16 out_y;
    mg_sdk_u16 word_x;
    mg_sdk_u16 sample;
    mg_sdk_u16 pixels[8];
    mg_sdk_u16 palette;
    mg_sdk_u16 data_base;
    mg_sdk_u32 read;
    catalog_string(entry_offset(entry), CATALOG_PATH_BYTES, path);
    clear_icon_pixels(slot);
    /* The recovery system menu is intentionally a text-only carousel item. */
    if (is_system_menu_entry(entry, path)) return 1;
    file = mg_sdk_resident_file_open(path, MG_SDK_FILE_OPEN_READ);
    if (file == MG_SDK_INVALID_FILE_HANDLE) return 0;
    if (mg_sdk_resident_file_seek_absolute(file, ICON_PALETTE_OFFSET) != 0 ||
        mg_sdk_resident_file_read(
            ICON_PRIMARY + slot * 16U, 32, file) != 32) {
        (void)mg_sdk_resident_file_close(file);
        return 0;
    }
    for (palette = 0; palette < 16U; ++palette)
        ICON_PRIMARY[slot * 16U + palette] =
            icon_color(ICON_PRIMARY[slot * 16U + palette]);
    data_base = (mg_sdk_u16)(HB_ICON_PALETTE_WORDS +
        slot * HB_ICON_ICON_WORDS);
    for (chunk = 0; chunk < 13U; ++chunk) {
        if (mg_sdk_resident_file_seek_absolute(
                file,
                ICON_SOURCE_OFFSET +
                    (mg_sdk_u32)chunk * ICON_CHUNK_ROWS * ICON_SOURCE_ROW_BYTES
            ) != 0) {
            (void)mg_sdk_resident_file_close(file);
            return 0;
        }
        read = mg_sdk_resident_file_read(
            ICON_TEMP, ICON_CHUNK_ROWS * ICON_SOURCE_ROW_BYTES, file);
        if (read != ICON_CHUNK_ROWS * ICON_SOURCE_ROW_BYTES) {
            (void)mg_sdk_resident_file_close(file);
            return 0;
        }
        for (out_y = 0; out_y < 64U; ++out_y) {
            mg_sdk_u16 source_y;
            mg_sdk_u16 row_byte;
            if (out_y < 6U || out_y >= 58U) continue;
            source_y = (mg_sdk_u16)((out_y - 6U) * 2U);
            if ((source_y >> 3) != chunk) continue;
            row_byte = (mg_sdk_u16)((source_y & 7U) * ICON_SOURCE_ROW_BYTES);
            for (word_x = 0; word_x < 4U; ++word_x) {
                for (sample = 0; sample < 8U; ++sample) {
                    mg_sdk_u16 output_x = (mg_sdk_u16)(word_x * 8U + sample);
                    mg_sdk_u16 source_byte = packed_byte(
                        ICON_TEMP, (mg_sdk_u16)(row_byte + output_x));
                    mg_sdk_u16 source_color = (source_byte >> 4) & 0x0fU;
                    pixels[sample] = ICON_PRIMARY[slot * 16U + source_color];
                }
                ICON_PRIMARY[data_base + out_y * 4U + word_x] =
                    mg_sdk_bitmap_pack_2bpp_word(pixels);
            }
        }
    }
    (void)mg_sdk_resident_file_close(file);
    return 1;
}

static void destroy_icons(void)
{
    mg_sdk_u16 slot;
    for (slot = 0; slot < CAROUSEL_SLOTS; ++slot) {
        if (ICON_HANDLES[slot] != MG_SDK_INVALID_UI_HANDLE)
            mg_sdk_ui_b_destroy(ICON_HANDLES[slot]);
        ICON_HANDLES[slot] = MG_SDK_INVALID_UI_HANDLE;
    }
    if (STATE[ST_ICON_SLOT] != 0xffffU) {
        mg_sdk_resident_unregister_dynamic_bundle(STATE[ST_ICON_SLOT]);
        STATE[ST_ICON_SLOT] = 0xffffU;
    }
}

static void rebuild_icons(void)
{
    static const mg_sdk_s16 position[3] = {54, 160, 266};
    mg_sdk_u16 slot;
    mg_sdk_u16 entry;
    destroy_icons();
    for (slot = 0; slot < HB_ICON_PRIMARY_WORD_COUNT; ++slot)
        ICON_PRIMARY[slot] = 0;
    for (slot = 0; slot < CAROUSEL_SLOTS; ++slot) {
        entry = visible_entry(slot);
        if (entry != 0xffffU) (void)load_mba_icon(entry, slot);
    }
    hb_icon_copy_bundle(ICON_GRAPH);
    STATE[ST_ICON_SLOT] = hb_icon_register(ICON_GRAPH, ICON_PRIMARY);
    if (STATE[ST_ICON_SLOT] == 0U || STATE[ST_ICON_SLOT] == 0xffffU) {
        STATE[ST_STATUS] = 0xe302U;
        return;
    }
    for (slot = 0; slot < CAROUSEL_SLOTS; ++slot) {
        entry = visible_entry(slot);
        if (entry == 0xffffU) continue;
        ICON_HANDLES[slot] = hb_icon_create(STATE[ST_ICON_SLOT]);
        if (ICON_HANDLES[slot] != MG_SDK_INVALID_UI_HANDLE) {
            struct mg_sdk_ui_b_object *object =
                (struct mg_sdk_ui_b_object *)mg_sdk_ui_b_get(ICON_HANDLES[slot]);
            if (object != 0) {
                mg_sdk_ui_b_object_prepare(object, position[slot],
                    slot == 1U ? 174 : 181, 0);
                mg_sdk_ui_b_object_show(object, 0, slot, position[slot],
                    slot == 1U ? 174 : 181);
            }
        }
    }
    STATE[ST_ICON_REFRESHES]++;
}

static void show_names(void)
{
    static const mg_sdk_u16 center[3] = {54, 160, 266};
    char title[CATALOG_TITLE_BYTES];
    mg_sdk_u16 slot;
    mg_sdk_u16 entry;
    mg_sdk_u16 capacity;
    mg_sdk_u16 length;
    clear_text();
    if (STATE[ST_ENTRY_COUNT] == 0) {
        add_text("NO APPS", 139, 214);
        return;
    }
    for (slot = 0; slot < CAROUSEL_SLOTS; ++slot) {
        entry = visible_entry(slot);
        if (entry == 0xffffU) continue;
        capacity = STATE[ST_CATALOG_STRIDE] == CATALOG_V1_ENTRY_BYTES
            ? 18U : CATALOG_TITLE_BYTES;
        if (slot != 1U && capacity > 10U) capacity = 10U;
        catalog_string(
            (mg_sdk_u16)(entry_offset(entry) + CATALOG_PATH_BYTES),
            capacity,
            title);
        length = text_length(title);
        add_text(title, (mg_sdk_u16)(center[slot] - length * 3U), 214);
    }
}

static void refresh_carousel(void)
{
    assign_visible_entries();
    rebuild_icons();
    show_names();
}

static void select_item(mg_sdk_u16 item)
{
    if (item >= STATE[ST_ENTRY_COUNT] || item == STATE[ST_SELECTED]) return;
    STATE[ST_SELECTED] = item;
    refresh_carousel();
}

static void select_previous(void)
{
    if (STATE[ST_ENTRY_COUNT] == 0) return;
    select_item(STATE[ST_SELECTED] == 0
        ? (mg_sdk_u16)(STATE[ST_ENTRY_COUNT] - 1U)
        : (mg_sdk_u16)(STATE[ST_SELECTED] - 1U));
}

static void select_next(void)
{
    mg_sdk_u16 item;
    if (STATE[ST_ENTRY_COUNT] == 0) return;
    item = (mg_sdk_u16)(STATE[ST_SELECTED] + 1U);
    if (item >= STATE[ST_ENTRY_COUNT]) item = 0;
    select_item(item);
}

static void launch_selected(void)
{
    if (STATE[ST_ENTRY_COUNT] == 0) return;
    catalog_string(entry_offset(STATE[ST_SELECTED]), CATALOG_PATH_BYTES, LAUNCH_PATH);
    if (LAUNCH_PATH[0] == 0 || !mg_sdk_resident_path_exists(LAUNCH_PATH)) {
        clear_text();
        add_text("APP MISSING", 130, 214);
        STATE[ST_STATUS] = 0xe305U;
        return;
    }
    STATE[ST_LAUNCH_PENDING] = 1;
    mg_sdk_resident_launch_mba(LAUNCH_PATH, 1, &launch_argument);
}

static void touch_event(void *user, const struct mg_sdk_touch_event *event)
{
    mg_sdk_u16 slot;
    mg_sdk_u16 item;
    (void)user;
    if (event->state == MG_SDK_TOUCH_STATE_SENTINEL) {
        if (STATE[ST_TOUCH_ITEM] != 0xffffU &&
            STATE[ST_TOUCH_WAS_SELECTED] != 0U) {
            STATE[ST_TOUCH_LAUNCHES]++;
            launch_selected();
        }
        STATE[ST_TOUCH_ITEM] = 0xffffU;
        STATE[ST_TOUCH_WAS_SELECTED] = 0;
        return;
    }
    if (event->y < 135) return;
    slot = event->x < 107 ? 0U : (event->x < 213 ? 1U : 2U);
    item = visible_entry(slot);
    if (item == 0xffffU) return;
    STATE[ST_TOUCH_ITEM] = item;
    STATE[ST_TOUCH_WAS_SELECTED] = item == STATE[ST_SELECTED];
    if (!STATE[ST_TOUCH_WAS_SELECTED]) select_item(item);
}

static void ensure_music(void)
{
    mg_sdk_u32 handle = state_handle(ST_MUSIC_LO);
    if (handle == MG_SDK_INVALID_UI_HANDLE) {
        /* repeat=1 is the resident/SPU loop control. Do not poll the short-lived
         * resident wrapper state and retrigger the same hardware channel. */
        handle = mg_sdk_resident_play_sound(3, 0x7f, 0x40, 1, 0);
        set_state_handle(ST_MUSIC_LO, handle);
        STATE[ST_MUSIC_RESTARTS]++;
    }
}

static int app_start(void)
{
    ensure_music();
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    struct mg_sdk_ui_b_object *wave;
    (void)ticks;
    STATE[ST_FRAME_COUNT]++;
    mg_sdk_direct_controls_poll(CONTROLS);
    if (WAVE_HANDLES[0] != MG_SDK_INVALID_UI_HANDLE) {
        wave = (struct mg_sdk_ui_b_object *)mg_sdk_ui_b_get(WAVE_HANDLES[0]);
        if (wave != 0)
            STATE[ST_WAVE_RECORD] = wave->word[MG_SDK_UI_B_OBJECT_WORD_RECORD];
    }
    if (STATE[ST_LAUNCH_PENDING]) return 0;
    mg_sdk_touch_poll(&mg_sdk_experimental_resident_touch_backend, 0, touch_event, 0);
    if (STATE[ST_LAUNCH_PENDING]) return 0;
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_LEFT)) select_previous();
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_RIGHT)) select_next();
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_PRIMARY)) launch_selected();
    return STATE[ST_LAUNCH_PENDING] ? 0 : 1;
}

static void app_stop(void)
{
    mg_sdk_u16 index;
    clear_text();
    mg_sdk_direct_controls_hide(CONTROLS);
    destroy_icons();
    for (index = 0; index < WAVE_SPRITES; ++index) {
        if (WAVE_HANDLES[index] != MG_SDK_INVALID_UI_HANDLE)
            mg_sdk_ui_b_destroy(WAVE_HANDLES[index]);
    }
    if (state_handle(ST_BACKGROUND_LO) != MG_SDK_INVALID_UI_HANDLE)
        mg_sdk_ui_a_destroy(state_handle(ST_BACKGROUND_LO));
}

int main(void)
{
    struct mg_sdk_runtime_callbacks callbacks;
    mg_sdk_u32 scratch = 0;
    mg_sdk_u16 index;
    mg_sdk_ui_handle background;
    for (index = 0; index < 32U; ++index) STATE[index] = 0;
    for (index = 0; index < TEXT_HANDLE_CAPACITY; ++index)
        TEXT_HANDLES[index] = MG_SDK_INVALID_UI_HANDLE;
    for (index = 0; index < WAVE_SPRITES; ++index)
        WAVE_HANDLES[index] = MG_SDK_INVALID_UI_HANDLE;
    for (index = 0; index < CAROUSEL_SLOTS; ++index)
        ICON_HANDLES[index] = MG_SDK_INVALID_UI_HANDLE;
    STATE[ST_TOUCH_ITEM] = 0xffffU;
    STATE[ST_ICON_SLOT] = 0xffffU;
    STATE[ST_STATUS] = 0x8300U;
    set_state_handle(ST_BACKGROUND_LO, MG_SDK_INVALID_UI_HANDLE);
    set_state_handle(ST_MUSIC_LO, MG_SDK_INVALID_UI_HANDLE);
    if (mg_sdk_resident_runtime_setup(&scratch) == 0) return 0;
    if (mg_sdk_direct_controls_init(CONTROLS) == 0) {
        mg_sdk_resident_runtime_finalize();
        return 0;
    }

    hb_wave_copy_bundle(WAVE_RAM);
    hb_wave_register(WAVE_RAM);
    background = hb_wave_create_background();
    set_state_handle(ST_BACKGROUND_LO, background);
    for (index = 0; index < WAVE_SPRITES; ++index) {
        mg_sdk_u16 column = index & 3U;
        mg_sdk_u16 row = index >> 2;
        struct mg_sdk_ui_b_object *object;
        WAVE_HANDLES[index] = hb_wave_create_sprite();
        if (WAVE_HANDLES[index] == MG_SDK_INVALID_UI_HANDLE) continue;
        object = (struct mg_sdk_ui_b_object *)mg_sdk_ui_b_get(WAVE_HANDLES[index]);
        if (object != 0) {
            mg_sdk_s16 x = (mg_sdk_s16)(40 + column * 80U);
            mg_sdk_s16 y = (mg_sdk_s16)(52 + row * 57U);
            mg_sdk_ui_b_object_prepare(object, x, y, 0);
            mg_sdk_ui_b_object_play_animation(
                object, HB_WAVE_MODE_WAVE, column, x, y, 1);
        }
    }

    mobigo_clean_font_copy_bundle(FONT_RAM);
    STATE[ST_FONT_SLOT] = mobigo_clean_font_register_dynamic(FONT_RAM);
    if (background == MG_SDK_INVALID_UI_HANDLE || STATE[ST_FONT_SLOT] == 0) {
        STATE[ST_STATUS] = 0xe301U;
        for (;;) mg_sdk_watchdog_kick();
    }

    STATE[ST_ENTRY_COUNT] = 0;
    if (!load_catalog_from(catalog_path))
        (void)load_catalog_from(emulator_catalog_path);
    STATE[ST_SELECTED] = 0;
    refresh_carousel();

    mg_sdk_audio_prepare_single_w_root(
        AUDIO_ROOT, (mg_sdk_u32)AUDIO_W_RECORD, (mg_sdk_u32)AUDIO_LAYOUT);
    mg_sdk_audio_prepare_w_pcm8(
        AUDIO_W_RECORD,
        HB_MUSIC_BYTE_COUNT,
        HB_MUSIC_SAMPLE_RATE,
        HB_MUSIC_SAMPLE_COUNT,
        0);
    mg_sdk_audio_prepare_wave_layout(
        AUDIO_LAYOUT, (mg_sdk_u32)hb_music_words, HB_MUSIC_WORD_COUNT);
    mg_sdk_resident_register_audio_resources(AUDIO_ROOT, 0);
    STATE[ST_STATUS] = 0x8301U;

    callbacks.start = app_start;
    callbacks.frame = app_frame;
    callbacks.stop = app_stop;
    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {}
    mg_sdk_resident_runtime_finalize();
    return 0;
}
