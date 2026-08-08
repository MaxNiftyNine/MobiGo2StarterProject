#ifndef MOBIGO_SDK_HARDWARE_H
#define MOBIGO_SDK_HARDWARE_H

#include "mobigo_sdk/input.h"

/*
 * Target-only low-level hardware helpers.
 *
 * Lifecycle applications should prefer the resident input, graphics, and UI
 * services.  These calls are for framebuffer-oriented programs which retain
 * the launcher's hardware setup and deliberately own their frame loop.  They
 * must not be called by host programs.
 */

enum {
    MG_SDK_LCD_WIDTH = 320,
    MG_SDK_LCD_HEIGHT = 240,
    MG_SDK_LCD_STRIDE_WORDS = 320,
    MG_SDK_DMA_CHANNELS = 4,
    MG_SDK_MATRIX_ROWS = 6,
    MG_SDK_MATRIX_COLUMNS = 9
};

#define MG_SDK_LCD_FRAME_WORDS ((mg_sdk_u32)0x00012c00UL)
#define MG_SDK_DMA_DEFAULT_TIMEOUT ((mg_sdk_u32)0x000fffffUL)

enum mg_sdk_dma_result {
    MG_SDK_DMA_OK = 0,
    MG_SDK_DMA_INVALID_ARGUMENT = -1,
    MG_SDK_DMA_TIMEOUT = -2
};

enum mg_sdk_dma_mode {
    MG_SDK_DMA_MODE_COPY = 0,
    MG_SDK_DMA_MODE_FIXED_SOURCE = 1
};

struct mg_sdk_framebuffers {
    mg_sdk_u32 front_word_address;
    mg_sdk_u32 back_word_address;
    mg_sdk_u16 width;
    mg_sdk_u16 height;
    mg_sdk_u16 stride_words;
};

struct mg_sdk_matrix_state {
    mg_sdk_u16 row[MG_SDK_MATRIX_ROWS];
};

/* Keep the inherited watchdog alive without changing its configuration. */
void mg_sdk_watchdog_kick(void);

/* Capture the launcher-owned RGB565 buffers.  Present keeps IRQ/FIQ enabled;
 * take_ownership additionally disables PPU frame interrupts before selecting
 * one stable scanout buffer. */
int mg_sdk_framebuffers_capture(struct mg_sdk_framebuffers *framebuffers);
void mg_sdk_framebuffer_present(mg_sdk_u32 word_address);
void mg_sdk_framebuffer_take_ownership(mg_sdk_u32 word_address);

/* Start is asynchronous and accepts only the two verified transfer modes.
 * Wait acknowledges the channel completion flag and services the watchdog
 * while polling.  Convenience copy/fill calls wait for completion. */
int mg_sdk_dma_start(
    mg_sdk_u16 channel,
    mg_sdk_u32 source_word_address,
    mg_sdk_u32 destination_word_address,
    mg_sdk_u32 word_count,
    enum mg_sdk_dma_mode mode);
int mg_sdk_dma_wait(mg_sdk_u16 channel, mg_sdk_u32 timeout);
int mg_sdk_dma_copy_words(
    mg_sdk_u16 channel,
    mg_sdk_u32 source_word_address,
    mg_sdk_u32 destination_word_address,
    mg_sdk_u32 word_count);
int mg_sdk_dma_fill_words(
    mg_sdk_u16 channel,
    mg_sdk_u16 value,
    mg_sdk_u32 destination_word_address,
    mg_sdk_u32 word_count);

/* Direct six-by-nine keyboard/button matrix access.  Scanning temporarily
 * drives one row and deactivates all rows before returning. */
void mg_sdk_matrix_init(void);
mg_sdk_u16 mg_sdk_matrix_scan_row(mg_sdk_u16 row);
void mg_sdk_matrix_scan(struct mg_sdk_matrix_state *state);
int mg_sdk_matrix_cell_down(
    const struct mg_sdk_matrix_state *state,
    mg_sdk_u16 row,
    mg_sdk_u16 column);

/* Translate the physical console buttons to the same game/system masks used
 * by resident_keys.h.  Keyboard cells remain available through cell_down. */
mg_sdk_u16 mg_sdk_matrix_game_keys(
    const struct mg_sdk_matrix_state *state);
mg_sdk_u16 mg_sdk_matrix_system_keys(
    const struct mg_sdk_matrix_state *state);

#endif
