#include "mobigo_sdk/mobigo_sdk.h"
#include "mobigo_clean_font_resources.h"
#include "hb_wave_resources.h"

#define SYSTEM_UI_RAM ((mg_sdk_u16 *)0x5000UL)
#define CONTROLS ((struct mg_sdk_standard_controls *)0x5800UL)
#define WAVE_RAM ((mg_sdk_u16 *)0x5840UL)
#define FONT_RAM ((mg_sdk_u16 *)0x5900UL)
#define TEXT_HANDLES ((mg_sdk_ui_handle *)0x6420UL)
#define STATE ((volatile mg_sdk_u16 *)0x64d0UL)
#define INDEX_BUFFER ((mg_sdk_u16 *)0x6500UL)
#define LAUNCH_PATH ((char *)0x6720UL)

#define INDEX_BUFFER_BYTES 1032U
#define CATALOG_HEADER_BYTES 8U
#define CATALOG_ENTRY_BYTES 64U
#define CATALOG_PATH_BYTES 42U
#define CATALOG_LABEL_BYTES 20U
#define CATALOG_MAX_ENTRIES 16U
#define PAGE_ROWS 3U
#define TEXT_HANDLE_CAPACITY 84U

enum {
    ST_FONT_SLOT = 0,
    ST_ENTRY_COUNT,
    ST_SELECTED,
    ST_TEXT_COUNT,
    ST_STATUS,
    ST_BACKGROUND_LO,
    ST_BACKGROUND_HI,
    ST_LAUNCH_PENDING
};

static const char catalog_path[] = "A:\\HB\\INDEX.HB";
/* The stock regional sort file is accepted only when it starts with HB01.
 * This permits a copied-NAND emulator fixture without adding a directory;
 * retail MBASORT data is rejected by the catalog parser. */
static const char emulator_catalog_path[] = "A:DEGER\\MBASORT.LST";
static const mg_sdk_u32 launch_argument = 999UL;

static mg_sdk_u32 background_handle(void)
{
    return (mg_sdk_u32)STATE[ST_BACKGROUND_LO] |
        ((mg_sdk_u32)STATE[ST_BACKGROUND_HI] << 16);
}

static void set_background_handle(mg_sdk_u32 handle)
{
    STATE[ST_BACKGROUND_LO] = (mg_sdk_u16)handle;
    STATE[ST_BACKGROUND_HI] = (mg_sdk_u16)(handle >> 16);
}

static mg_sdk_u16 catalog_byte(mg_sdk_u16 offset)
{
    mg_sdk_u16 word = INDEX_BUFFER[offset >> 1];
    return (offset & 1U) ? (word >> 8) & 0xffU : word & 0xffU;
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

static int catalog_valid(mg_sdk_u32 size)
{
    mg_sdk_u16 count;
    mg_sdk_u16 stride;
    if (size < CATALOG_HEADER_BYTES || size > INDEX_BUFFER_BYTES) return 0;
    if (catalog_byte(0) != 'H' || catalog_byte(1) != 'B' ||
        catalog_byte(2) != '0' || catalog_byte(3) != '1') return 0;
    count = (mg_sdk_u16)(catalog_byte(4) | (catalog_byte(5) << 8));
    stride = (mg_sdk_u16)(catalog_byte(6) | (catalog_byte(7) << 8));
    if (count > CATALOG_MAX_ENTRIES || stride != CATALOG_ENTRY_BYTES) return 0;
    if ((mg_sdk_u32)CATALOG_HEADER_BYTES +
        (mg_sdk_u32)count * CATALOG_ENTRY_BYTES > size) return 0;
    STATE[ST_ENTRY_COUNT] = count;
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
    return (mg_sdk_u16)(CATALOG_HEADER_BYTES + entry * CATALOG_ENTRY_BYTES);
}

static void clear_text(void)
{
    if (STATE[ST_TEXT_COUNT] != 0 && STATE[ST_TEXT_COUNT] != 0xffffU) {
        mobigo_clean_font_destroy_text(TEXT_HANDLES, STATE[ST_TEXT_COUNT]);
    }
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
        STATE[ST_STATUS] = 0xe104U;
        return;
    }
    STATE[ST_TEXT_COUNT] = (mg_sdk_u16)(used + count);
}

static void show_catalog(void)
{
    mg_sdk_u16 page;
    mg_sdk_u16 row;
    mg_sdk_u16 item;
    mg_sdk_u16 base;
    char line[21];
    clear_text();
    add_text("HOMEBREW", 8, 18);
    if (STATE[ST_ENTRY_COUNT] == 0) {
        add_text("NO APPS FOUND", 8, 82);
        add_text("CONNECT MANAGER", 8, 112);
        return;
    }
    page = (mg_sdk_u16)(STATE[ST_SELECTED] / PAGE_ROWS);
    for (row = 0; row < PAGE_ROWS; ++row) {
        item = (mg_sdk_u16)(page * PAGE_ROWS + row);
        if (item >= STATE[ST_ENTRY_COUNT]) break;
        line[0] = item == STATE[ST_SELECTED] ? '>' : ' ';
        base = (mg_sdk_u16)(entry_offset(item) + CATALOG_PATH_BYTES);
        catalog_string(base, 20, line + 1);
        add_text(line, 8, (mg_sdk_u16)(70 + row * 34));
    }
    add_text("UP DOWN OPEN", 8, 210);
}

static void select_previous(void)
{
    if (STATE[ST_ENTRY_COUNT] == 0) return;
    if (STATE[ST_SELECTED] == 0)
        STATE[ST_SELECTED] = (mg_sdk_u16)(STATE[ST_ENTRY_COUNT] - 1U);
    else --STATE[ST_SELECTED];
    show_catalog();
}

static void select_next(void)
{
    if (STATE[ST_ENTRY_COUNT] == 0) return;
    ++STATE[ST_SELECTED];
    if (STATE[ST_SELECTED] >= STATE[ST_ENTRY_COUNT]) STATE[ST_SELECTED] = 0;
    show_catalog();
}

static void launch_selected(void)
{
    mg_sdk_u16 base;
    if (STATE[ST_ENTRY_COUNT] == 0) return;
    base = entry_offset(STATE[ST_SELECTED]);
    catalog_string(base, CATALOG_PATH_BYTES, LAUNCH_PATH);
    if (LAUNCH_PATH[0] == 0 || !mg_sdk_resident_path_exists(LAUNCH_PATH)) {
        clear_text();
        add_text("APP IS MISSING", 8, 90);
        add_text("EXIT TO RETURN", 8, 124);
        STATE[ST_STATUS] = 0xe105U;
        return;
    }
    STATE[ST_LAUNCH_PENDING] = 1;
    mg_sdk_resident_launch_mba(LAUNCH_PATH, 1, &launch_argument);
}

static int app_start(void)
{
    return 1;
}

static int app_frame(mg_sdk_u32 ticks)
{
    (void)ticks;
    mg_sdk_standard_controls_poll(CONTROLS);
    if (STATE[ST_LAUNCH_PENDING]) return 0;
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_UP)) select_previous();
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_DOWN)) select_next();
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_LEFT)) {
        mg_sdk_u16 step = STATE[ST_SELECTED] % PAGE_ROWS;
        while (step-- != 0) select_previous();
        select_previous();
    }
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_RIGHT)) {
        mg_sdk_u16 step = (mg_sdk_u16)(PAGE_ROWS -
            (STATE[ST_SELECTED] % PAGE_ROWS));
        while (step-- != 0) select_next();
    }
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_PRIMARY))
        launch_selected();
    if (mg_sdk_resident_game_key_pressed(MG_SDK_GAME_KEY_EXIT) &&
        STATE[ST_STATUS] == 0xe105U) {
        STATE[ST_STATUS] = 0x8001U;
        show_catalog();
    }
    return STATE[ST_LAUNCH_PENDING] ? 0 : 1;
}

static void app_stop(void)
{
    clear_text();
    mg_sdk_standard_controls_hide(CONTROLS);
    if (background_handle() != MG_SDK_INVALID_UI_HANDLE)
        mg_sdk_ui_a_destroy(background_handle());
}

int main(void)
{
    struct mg_sdk_runtime_callbacks callbacks;
    mg_sdk_u32 scratch = 0;
    mg_sdk_u16 index;
    mg_sdk_ui_handle background;

    for (index = 0; index < 16U; ++index) STATE[index] = 0;
    STATE[ST_STATUS] = 0x8000U;
    set_background_handle(MG_SDK_INVALID_UI_HANDLE);
    if (mg_sdk_resident_runtime_setup(&scratch) == 0) return 0;
    if (mg_sdk_standard_controls_init(CONTROLS, SYSTEM_UI_RAM) == 0) {
        mg_sdk_resident_runtime_finalize();
        return 0;
    }

    hb_wave_copy_bundle(WAVE_RAM);
    hb_wave_register(WAVE_RAM);
    background = hb_wave_create();
    set_background_handle(background);
    mobigo_clean_font_copy_bundle(FONT_RAM);
    STATE[ST_FONT_SLOT] = mobigo_clean_font_register_dynamic(FONT_RAM);
    if (background == MG_SDK_INVALID_UI_HANDLE || STATE[ST_FONT_SLOT] == 0) {
        STATE[ST_STATUS] = 0xe101U;
        for (;;) mg_sdk_watchdog_kick();
    }

    STATE[ST_ENTRY_COUNT] = 0;
    if (!load_catalog_from(catalog_path))
        (void)load_catalog_from(emulator_catalog_path);
    STATE[ST_SELECTED] = 0;
    show_catalog();
    STATE[ST_STATUS] = 0x8001U;

    callbacks.start = app_start;
    callbacks.frame = app_frame;
    callbacks.stop = app_stop;
    while (mg_sdk_resident_runtime_step(&callbacks) != 0) {}
    mg_sdk_resident_runtime_finalize();
    return 0;
}
