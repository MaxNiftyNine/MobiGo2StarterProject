/*
 * Celeste Classic for the VTech MobiGo 2.
 *
 * The game logic is a target adaptation of ccleste, a direct C translation
 * of the original PICO-8 cartridge. This file implements the PICO-8 drawing
 * and input surface plus the hardware-safe LD application entry loop.
 */

#include "celeste.h"
#include "frontend.h"
#include "assets.h"

#define REG16(address) (*(volatile unsigned short *)(address))
#define WORD_PTR(address) ((volatile unsigned short *)(address))

#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 240
#define PICO_WIDTH 128
#define PICO_HEIGHT 128
#define DISPLAY_WIDTH 240
#define DISPLAY_BORDER 40

#define PICO_PIXELS (PICO_WIDTH * PICO_HEIGHT)
#define PICO_BUFFER_WORDS (PICO_PIXELS / 4)
#define PICO_BUFFER_ADDRESS 0x5000UL
#define RGB_TABLE_ADDRESS 0x60e0UL
#define ROW_BUFFER_ADDRESS 0x6100UL
#define ROW_BUFFER_ALT_ADDRESS 0x6240UL
#define PICO_BUFFER WORD_PTR(PICO_BUFFER_ADDRESS)
#define RGB_TABLE WORD_PTR(RGB_TABLE_ADDRESS)
#define ROW_BUFFER WORD_PTR(ROW_BUFFER_ADDRESS)
#define ROW_BUFFER_ALT WORD_PTR(ROW_BUFFER_ALT_ADDRESS)

/*
 * Keep CPU-written render scratch in the directly addressed internal RAM
 * window that is known to work for an LD-launched MBA.
 *
 * 0x18000 is not a safe private framebuffer assumption: CPU access to that
 * extended range depends on inherited memory-controller state.  The previous
 * attempted fix made the same mistake for the DMA staging row at 0x1c000,
 * which is why the emulator showed an entire frame of coloured garbage.
 *
 * The PICO-8 image is packed as four 4-bit palette indices per word, occupying
 * 0x5000..0x5fff.  Two expanded RGB565 rows use 0x6100..0x637f, below the
 * inherited firmware stack observed above 0x6a00. CelestePico8G1.bdy caps
 * linker-owned RAM at 0x4fff, so compiler globals cannot overlap the scratch
 * blocks.
 */
#if PICO_BUFFER_ADDRESS + PICO_BUFFER_WORDS > ROW_BUFFER_ADDRESS
#error render scratch buffers overlap
#endif
#if RGB_TABLE_ADDRESS + 16 > ROW_BUFFER_ADDRESS
#error RGB table overlaps DMA staging row
#endif
#if ROW_BUFFER_ADDRESS + SCREEN_WIDTH > ROW_BUFFER_ALT_ADDRESS
#error DMA staging rows overlap
#endif
#if ROW_BUFFER_ALT_ADDRESS + SCREEN_WIDTH > 0x6800UL
#error DMA staging rows approach inherited firmware stack area
#endif

static const unsigned short pico_rgb565[16] = {
    0x0000,0x194a,0x792a,0x042a,
    0xaa86,0x5aa9,0xc618,0xff9d,
    0xf809,0xfd00,0xff64,0x0726,
    0x2d7f,0x83b3,0xfbb5,0xfe75
};

static unsigned short palette_map[16];
static unsigned short palette_identity;
static int camera_x;
static int camera_y;
static unsigned buttons_state;

extern void expand_row_fast(int source_y, unsigned short row_address);

static int gfx_pixel(int index)
{
    unsigned short word = celeste_gfx_packed[index >> 2];
    return (word >> ((index & 3) * 4)) & 15;
}

static int font_pixel(int index)
{
    unsigned short word = celeste_font_packed[index >> 4];
    return (word >> (index & 15)) & 1;
}

static int map_byte(int index)
{
    unsigned short word = celeste_tilemap_packed[index >> 1];
    return (word >> ((index & 1) * 8)) & 0xff;
}

static int flag_byte(int index)
{
    unsigned short word = celeste_tile_flags_packed[index >> 1];
    return (word >> ((index & 1) * 8)) & 0xff;
}

/* Keep this first. The packer overwrites the MBA entry with a far jump. */
void mba_entry_reserve(void)
{
    REG16(0x780b) = 0xa005;
    REG16(0x780a) = 0x0000;
}

static void service_watchdog(void)
{
    REG16(0x780b) = 0xa005;
}

static void assert_scanout(unsigned short low, unsigned short high)
{
    REG16(0x7078) = low & 0xfff0u;
    REG16(0x7079) = high & 0x07ffu;
    REG16(0x707a) = low & 0xfff0u;
    REG16(0x707b) = high & 0x07ffu;
    REG16(0x707f) = 0x0088u;
}

/*
 * The retail launcher owns IRQ5 and can rotate FBI/FBO behind an LD
 * application. Take ownership of the video source only, while leaving CPU
 * IRQ/FIQ enabled for the rest of the inherited runtime. This makes one
 * framebuffer sufficient and removes a full 76800-word copy every frame.
 */
static void take_video_ownership(unsigned short low, unsigned short high)
{
    REG16(0x7062) = 0;
    REG16(0x7063) = 0xffffu;
    assert_scanout(low, high);
}

static void start_dma(unsigned channel, unsigned long source,
                      unsigned long destination, unsigned long count,
                      unsigned short control)
{
    unsigned long base = 0x7a80UL + (unsigned long)channel * 8UL;
    unsigned short flag = (unsigned short)(1u << channel);
    REG16(base) = 0x0200u;
    REG16(0x7abf) = flag;
    REG16(base + 1u) = (unsigned short)(source & 0xffffUL);
    REG16(base + 4u) = (unsigned short)((source >> 16) & 0x07ffUL);
    REG16(base + 2u) = (unsigned short)(destination & 0xfff0UL);
    REG16(base + 5u) = (unsigned short)((destination >> 16) & 0x07ffUL);
    REG16(base + 3u) = (unsigned short)(count & 0xffffUL);
    REG16(base + 6u) = (unsigned short)((count >> 16) & 0x07ffUL);
    REG16(base) = control;
}

static void wait_dma(unsigned channel)
{
    unsigned long timeout;
    unsigned short flag = (unsigned short)(1u << channel);
    timeout = 0x000fffffUL;
    while (!(REG16(0x7abf) & flag) && timeout) {
        --timeout;
        if ((timeout & 0x0fffUL) == 0) service_watchdog();
    }
    REG16(0x7abf) = flag;
}

static void fill_words(unsigned short value, unsigned long destination,
                       unsigned long count)
{
    *WORD_PTR(destination) = value;
    /* Source step field 0x80 means fixed source; destination increments. */
    start_dma(0, destination, destination, count, 0x0089u);
    wait_dma(0);
}

static void deactivate_rows(void)
{
    REG16(0x7870) &= (unsigned short)~0x06e0u;
    REG16(0x7880) &= (unsigned short)~0x0004u;
}

static unsigned short read_matrix_columns(void)
{
    unsigned short b = REG16(0x7868);
    unsigned short a = REG16(0x7860);
    return (unsigned short)(((b >> 10) & 0x003fu) |
                            ((a >> 5) & 0x01c0u));
}

static unsigned short scan_row(unsigned row)
{
    volatile unsigned settle;
    unsigned short bit;
    deactivate_rows();
    if (row == 0) bit = 0x0080u;
    else if (row == 1) bit = 0x0040u;
    else if (row == 2) bit = 0x0400u;
    else if (row == 3) bit = 0x0200u;
    else if (row == 4) bit = 0x0020u;
    else bit = 0;
    if (row < 5) {
        REG16(0x7873) |= bit;
        REG16(0x7872) |= bit;
        REG16(0x7870) |= bit;
    } else {
        REG16(0x7883) |= 0x0004u;
        REG16(0x7882) |= 0x0004u;
        REG16(0x7880) |= 0x0004u;
    }
    for (settle = 0; settle < 16u; ++settle) { }
    return read_matrix_columns();
}

static void input_init(void)
{
    REG16(0x7862) &= (unsigned short)~0x3800u;
    REG16(0x786a) &= (unsigned short)~0xfc00u;
    deactivate_rows();
}

static unsigned read_buttons(void)
{
    unsigned short r0 = scan_row(0);
    unsigned short r1 = scan_row(1);
    unsigned short r2 = scan_row(2);
    unsigned short r3 = scan_row(3);
    unsigned short r4 = scan_row(4);
    unsigned result = 0;

    if ((r1 & (1u << 6)) || (r3 & (1u << 3)) ||
        (r3 & (1u << 0))) result |= 1u << 0;
    if ((r1 & (1u << 8)) || (r4 & (1u << 3)) ||
        (r4 & (1u << 0))) result |= 1u << 1;
    if ((r0 & (1u << 6)) || (r3 & (1u << 4))) result |= 1u << 2;
    if ((r1 & (1u << 7)) || (r4 & (1u << 4))) result |= 1u << 3;
    if ((r0 & (1u << 7)) || (r3 & (1u << 5)) ||
        (r4 & (1u << 1))) result |= 1u << 4;
    if ((r2 & (1u << 8)) || (r3 & (1u << 1)) ||
        (r4 & (1u << 5)) || (r4 & (1u << 6))) result |= 1u << 5;
    deactivate_rows();
    return result;
}

static void set_pixel_index(int x, int y, unsigned short index_color)
{
    unsigned index;
    unsigned shift;
    unsigned short mask;
    volatile unsigned short *word;
    if (x < 0 || x >= PICO_WIDTH || y < 0 || y >= PICO_HEIGHT) return;
    index = (unsigned)(y * PICO_WIDTH + x);
    shift = (index & 3u) * 4u;
    mask = (unsigned short)(0x000fu << shift);
    word = PICO_BUFFER + (index >> 2);
    *word = (unsigned short)((*word & (unsigned short)~mask) |
                             (unsigned short)((index_color & 15u) << shift));
}

static void put_pixel(int x, int y, int color)
{
    set_pixel_index(x, y, palette_map[color & 15] & 15u);
}

static unsigned short reverse_nibbles(unsigned short value)
{
    return (unsigned short)(((value & 0x000fu) << 12) |
                            ((value & 0x00f0u) << 4) |
                            ((value & 0x0f00u) >> 4) |
                            ((value & 0xf000u) >> 12));
}

static void blend_sprite_word(unsigned short source,
                              volatile unsigned short *destination)
{
    unsigned short mapped;
    unsigned short keep = 0;
    if (palette_identity) {
        /*
         * Most tiles use the identity palette. Fully opaque packed words can
         * replace the destination directly; transparent words only need one
         * destination read and no palette lookups.
         */
        if ((source & 0x000fu) && (source & 0x00f0u) &&
            (source & 0x0f00u) && (source & 0xf000u)) {
            *destination = source;
            return;
        }
        mapped = source;
    } else {
        mapped = 0;
        if (source & 0x000fu) mapped |= palette_map[source & 0x000fu];
        if (source & 0x00f0u)
            mapped |= (unsigned short)(palette_map[(source >> 4) & 15u] << 4);
        if (source & 0x0f00u)
            mapped |= (unsigned short)(palette_map[(source >> 8) & 15u] << 8);
        if (source & 0xf000u)
            mapped |= (unsigned short)(palette_map[(source >> 12) & 15u] << 12);
    }
    if (!(source & 0x000fu)) keep |= 0x000fu;
    if (!(source & 0x00f0u)) keep |= 0x00f0u;
    if (!(source & 0x0f00u)) keep |= 0x0f00u;
    if (!(source & 0xf000u)) keep |= 0xf000u;
    *destination = (unsigned short)((*destination & keep) | mapped);
}

static void draw_sprite_tile(int tile, int x, int y, int flip_x, int flip_y)
{
    int py;
    int px;
    int source_x = (tile & 15) * 8;
    int source_y = (tile >> 4) * 8;
    x -= camera_x;
    y -= camera_y;
    if (tile < 0 || tile >= 128) return;
    if (x <= -8 || x >= PICO_WIDTH || y <= -8 || y >= PICO_HEIGHT) return;

    /*
     * Tiles and the room camera are normally four-pixel aligned. Blend their
     * packed source words directly instead of unpacking, clipping, mapping,
     * and read/modify/writing all 64 pixels independently.
     */
    if ((x & 3) == 0) {
        for (py = 0; py < 8; py++) {
            int screen_y = y + py;
            int sy;
            const unsigned short *source;
            unsigned short left;
            unsigned short right;
            if (screen_y < 0 || screen_y >= PICO_HEIGHT) continue;
            sy = source_y + (flip_y ? 7 - py : py);
            source = celeste_gfx_packed + sy * (PICO_WIDTH / 4) +
                     (source_x / 4);
            left = source[0];
            right = source[1];
            if (flip_x) {
                unsigned short swap = reverse_nibbles(left);
                left = reverse_nibbles(right);
                right = swap;
            }
            if (x >= 0 && x <= PICO_WIDTH - 4) {
                blend_sprite_word(
                    left, PICO_BUFFER + screen_y * (PICO_WIDTH / 4) + x / 4);
            }
            if (x + 4 >= 0 && x + 4 <= PICO_WIDTH - 4) {
                blend_sprite_word(
                    right, PICO_BUFFER + screen_y * (PICO_WIDTH / 4) +
                           (x + 4) / 4);
            }
        }
        return;
    }

    for (py = 0; py < 8; py++) {
        int sy = source_y + (flip_y ? 7 - py : py);
        for (px = 0; px < 8; px++) {
            int sx = source_x + (flip_x ? 7 - px : px);
            int color = gfx_pixel(sy * 128 + sx);
            if (color) put_pixel(x + px, y + py, color);
        }
    }
}

void mg_music(int track, int fade, int mask)
{
    (void)track;
    (void)fade;
    (void)mask;
}

void mg_spr(int sprite, int x, int y, int cols, int rows, int flipx, int flipy)
{
    int row;
    int col;
    for (row = 0; row < rows; row++) {
        for (col = 0; col < cols; col++) {
            draw_sprite_tile(sprite + row * 16 + col, x + col * 8,
                             y + row * 8, flipx, flipy);
        }
    }
}

int mg_btn(int button)
{
    if (button < 0 || button > 5) return 0;
    return (buttons_state & (1u << button)) != 0;
}

void mg_sfx(int id)
{
    (void)id;
}

void mg_pal(int source, int destination)
{
    int i;
    if (source >= 0 && source < 16 && destination >= 0 && destination < 16) {
        palette_map[source] = (unsigned short)destination;
        palette_identity = 1;
        for (i = 0; i < 16; i++) {
            if (palette_map[i] != (unsigned short)i) {
                palette_identity = 0;
                break;
            }
        }
    }
}

void mg_pal_reset(void)
{
    int i;
    for (i = 0; i < 16; i++) palette_map[i] = (unsigned short)i;
    palette_identity = 1;
}

void mg_rectfill(int x0, int y0, int x1, int y1, int color)
{
    int x;
    int y;
    unsigned short mapped;
    unsigned short packed;
    x0 -= camera_x;
    x1 -= camera_x;
    y0 -= camera_y;
    y1 -= camera_y;
    if (x0 > x1 || y0 > y1) return;
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 >= PICO_WIDTH) x1 = PICO_WIDTH - 1;
    if (y1 >= PICO_HEIGHT) y1 = PICO_HEIGHT - 1;
    mapped = palette_map[color & 15] & 15u;
    packed = (unsigned short)(mapped | (mapped << 4) |
                              (mapped << 8) | (mapped << 12));
    if (x0 == 0 && y0 == 0 &&
        x1 == PICO_WIDTH - 1 && y1 == PICO_HEIGHT - 1) {
        fill_words(packed, PICO_BUFFER_ADDRESS, PICO_BUFFER_WORDS);
        return;
    }
    for (y = y0; y <= y1; y++) {
        volatile unsigned short *word;
        x = x0;
        while (x <= x1 && (x & 3)) set_pixel_index(x++, y, mapped);
        word = PICO_BUFFER + y * (PICO_WIDTH / 4) + x / 4;
        while (x + 3 <= x1) {
            *word++ = packed;
            x += 4;
        }
        while (x <= x1) set_pixel_index(x++, y, mapped);
    }
}

static void line_screen(int x0, int y0, int x1, int y1, int color)
{
    int dx;
    int sx;
    int dy;
    int sy;
    int error;
    int twice;
    dx = x1 > x0 ? x1 - x0 : x0 - x1;
    sx = x0 < x1 ? 1 : -1;
    dy = y1 > y0 ? y0 - y1 : y1 - y0;
    sy = y0 < y1 ? 1 : -1;
    error = dx + dy;
    for (;;) {
        put_pixel(x0, y0, color);
        if (x0 == x1 && y0 == y1) break;
        twice = error * 2;
        if (twice >= dy) {
            error += dy;
            x0 += sx;
        }
        if (twice <= dx) {
            error += dx;
            y0 += sy;
        }
    }
}

void mg_line(int x0, int y0, int x1, int y1, int color)
{
    line_screen(x0 - camera_x, y0 - camera_y,
                x1 - camera_x, y1 - camera_y, color);
}

void mg_circfill(int x, int y, int radius, int color)
{
    int dy;
    int dx;
    int radius_squared = radius * radius;
    for (dy = -radius; dy <= radius; dy++) {
        dx = radius;
        while (dx > 0 &&
               dx * dx + dy * dy > radius_squared + radius) dx--;
        mg_rectfill(x - dx, y + dy, x + dx, y + dy, color);
    }
}

void mg_print(const char *text, int x, int y, int color)
{
    int py;
    int px;
    x -= camera_x;
    y -= camera_y;
    while (*text) {
        unsigned code = ((unsigned)*text++) & 0x7fu;
        int source_x = (code & 15u) * 8;
        int source_y = (code >> 4) * 8;
        for (py = 0; py < 8; py++) {
            for (px = 0; px < 8; px++) {
                if (font_pixel((source_y + py) * 128 + source_x + px)) {
                    put_pixel(x + px, y + py, color);
                }
            }
        }
        x += 4;
    }
}

int mg_mget(int x, int y)
{
    if (x < 0 || x >= 128 || y < 0 || y >= 64) return 0;
    return map_byte(y * 128 + x);
}

int mg_fget(int tile, int flag)
{
    if (tile < 0 || tile >= 128 || flag < 0 || flag > 7) return 0;
    return (flag_byte(tile) & (1u << flag)) != 0;
}

void mg_camera(int x, int y)
{
    camera_x = x;
    camera_y = y;
}

void mg_map(int mx, int my, int tx, int ty, int mw, int mh, int mask)
{
    int x;
    int y;
    for (y = 0; y < mh; y++) {
        for (x = 0; x < mw; x++) {
            int tile = mg_mget(mx + x, my + y);
            int flags = flag_byte(tile);
            int visible = mask == 0;
            if (mask == 4 && flags == 4) visible = 1;
            else if (mask != 0 && mask != 4 &&
                     (flags & (1u << (mask - 1)))) visible = 1;
            if (visible) draw_sprite_tile(tile, tx + x * 8, ty + y * 8, 0, 0);
        }
    }
}

static void clear_pico_buffer(void)
{
    int i;
    for (i = 0; i < PICO_BUFFER_WORDS; i++) PICO_BUFFER[i] = 0;
}

static void clear_row_borders(void)
{
    int i;
    for (i = 0; i < DISPLAY_BORDER; i++) {
        ROW_BUFFER[i] = 0;
        ROW_BUFFER_ALT[i] = 0;
    }
    for (i = DISPLAY_BORDER + DISPLAY_WIDTH; i < SCREEN_WIDTH; i++) {
        ROW_BUFFER[i] = 0;
        ROW_BUFFER_ALT[i] = 0;
    }
}

static void init_rgb_table(void)
{
    int i;
    for (i = 0; i < 16; i++) RGB_TABLE[i] = pico_rgb565[i];
}

/*
 * Scale 128x128 to a centered 240x240 square. A source row is expanded once
 * into a scratch row, then DMA reuses it for the one or two LCD rows that
 * select that source row. Two staging rows let the CPU expand row N+1 while
 * the real DMA controller transfers row N to SDRAM.
 */
static void present_frame(unsigned short fbi_low, unsigned short fbi_high)
{
    unsigned long destination =
        ((unsigned long)(fbi_high & 0x07ffu) << 16) |
        (unsigned long)(fbi_low & 0xfff0u);
    unsigned long current_address = ROW_BUFFER_ADDRESS;
    unsigned long next_address = ROW_BUFFER_ALT_ADDRESS;
    int source_y;

    expand_row_fast(0, (unsigned short)current_address);
    for (source_y = 0; source_y < PICO_HEIGHT; source_y++) {
        int repeats = (source_y & 7) < 7 ? 2 : 1;
        start_dma(0, current_address, destination, SCREEN_WIDTH, 0x0009u);

        /*
         * On hardware the DMA runs concurrently. The emulator completes it
         * synchronously, preserving deterministic validation.
         */
        if (source_y + 1 < PICO_HEIGHT) {
            expand_row_fast(source_y + 1, (unsigned short)next_address);
        }
        wait_dma(0);
        destination += SCREEN_WIDTH;

        if (repeats == 2) {
            start_dma(0, current_address, destination,
                      SCREEN_WIDTH, 0x0009u);
            wait_dma(0);
            destination += SCREEN_WIDTH;
        }

        {
            unsigned long swap_address = current_address;
            current_address = next_address;
            next_address = swap_address;
        }
        service_watchdog();
    }
    assert_scanout(fbi_low, fbi_high);
}

int main(void)
{
    unsigned short fbi_low;
    unsigned short fbi_high;

    service_watchdog();
    fbi_low = REG16(0x7078);
    fbi_high = REG16(0x7079);
    take_video_ownership(fbi_low, fbi_high);
    input_init();
    mg_pal_reset();
    camera_x = 0;
    camera_y = 0;
    buttons_state = 0;
    clear_pico_buffer();
    Celeste_P8_hard_reset();
    Celeste_P8_set_rndseed(1UL);
    Celeste_P8_init();
    init_rgb_table();
    clear_row_borders();

    for (;;) {
        service_watchdog();
        buttons_state = read_buttons();
        Celeste_P8_update();
        Celeste_P8_draw();
        present_frame(fbi_low, fbi_high);
    }
}
