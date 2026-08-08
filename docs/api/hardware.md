# Target-only low-level hardware API

`mobigo_sdk/hardware.h` is for framebuffer-oriented programs that deliberately
retain the launcher's setup and own their frame loop. Resident-lifecycle
applications should prefer resident input, graphics, and UI services.

These functions must not execute in a host process.

## Watchdog

```c
void mg_sdk_watchdog_kick(void);
```

This keeps the inherited watchdog alive without changing its configuration.
Call it during long low-level loops and while waiting for bounded hardware work.

## Inherited framebuffers

```c
struct mg_sdk_framebuffers {
    mg_sdk_u32 front_word_address;
    mg_sdk_u32 back_word_address;
    mg_sdk_u16 width;
    mg_sdk_u16 height;
    mg_sdk_u16 stride_words;
};

int mg_sdk_framebuffers_capture(struct mg_sdk_framebuffers *framebuffers);
void mg_sdk_framebuffer_present(mg_sdk_u32 word_address);
void mg_sdk_framebuffer_take_ownership(mg_sdk_u32 word_address);
```

Capture returns the launcher-selected front/back RGB565 word addresses plus
320×240 geometry and stride. Present preserves inherited IRQ/FIQ operation.
Taking ownership additionally disables PPU frame interrupts before choosing one
stable scanout buffer; use it only when the port intentionally replaces the
resident display path.

Capture returns 1 only when both inherited addresses are nonzero. Framebuffer
addresses must be 16-word aligned. Never substitute a fixed SDRAM address for
capture.

## System DMA

```c
enum mg_sdk_dma_mode {
    MG_SDK_DMA_MODE_COPY = 0,
    MG_SDK_DMA_MODE_FIXED_SOURCE = 1
};

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
```

The API supports asynchronous start/wait and synchronous copy/fill helpers over
channels `0..3`. Addresses and counts are 16-bit words. A destination must be
16-word aligned. Copy validates both source and destination ranges; fixed-source
mode validates the single source word and complete destination range.

| Result | Meaning |
| --- | --- |
| `MG_SDK_DMA_OK` | transfer started/completed as appropriate |
| `MG_SDK_DMA_INVALID_ARGUMENT` | bad channel/mode/range/alignment or zero count |
| `MG_SDK_DMA_TIMEOUT` | bounded wait expired |

`mg_sdk_dma_wait()` acknowledges completion and services the watchdog while
polling. Results distinguish success, invalid arguments, and timeout. Treat a
timeout as a real failure; do not continue rendering with a partially updated
buffer.

Use `MG_SDK_DMA_DEFAULT_TIMEOUT` with the synchronous helpers unless a measured
port requires another bound. `mg_sdk_dma_fill_words()` owns the SDK scratch word
at `MG_SDK_HARDWARE_SCRATCH_WORD_ADDRESS`; project arenas must not overlap it.

## Raw 6×9 matrix

```c
struct mg_sdk_matrix_state {
    mg_sdk_u16 row[MG_SDK_MATRIX_ROWS];
};

void mg_sdk_matrix_init(void);
mg_sdk_u16 mg_sdk_matrix_scan_row(mg_sdk_u16 row);
void mg_sdk_matrix_scan(struct mg_sdk_matrix_state *state);
int mg_sdk_matrix_cell_down(
    const struct mg_sdk_matrix_state *state,
    mg_sdk_u16 row,
    mg_sdk_u16 column);
mg_sdk_u16 mg_sdk_matrix_game_keys(
    const struct mg_sdk_matrix_state *state);
mg_sdk_u16 mg_sdk_matrix_system_keys(
    const struct mg_sdk_matrix_state *state);
```

The matrix helpers initialize GPIO scanning, read one row, capture all rows,
test a cell, and translate physical console buttons into the same logical game
and system masks used by resident keys.

Keyboard cells remain available through `mg_sdk_matrix_cell_down()`. Raw matrix
input needs application debouncing. Prefer resident edge queries whenever the
resident frame pump is active.

For standard system-button behavior in the same direct loop, prefer
`direct_controls.h`: it adds edge detection, resident setting persistence and
application, and the terminal power request without attempting resident UI.

## Constants and memory

`MG_SDK_LCD_WIDTH`, `MG_SDK_LCD_HEIGHT`, and
`MG_SDK_LCD_STRIDE_WORDS` are 320, 240, and 320. One RGB565 frame occupies
`MG_SDK_LCD_FRAME_WORDS` words. Matrix and DMA dimensions are exposed by
`MG_SDK_MATRIX_ROWS`, `MG_SDK_MATRIX_COLUMNS`, and `MG_SDK_DMA_CHANNELS`.

`memory_map.h` defines the conservative title arena and default UI/control
reservations. Treat its addresses as word addresses and use
`MG_SDK_WORD_RANGES_OVERLAP` when assigning project arenas.

## Ownership warning

Low-level framebuffer ownership, raw scanning, and resident UI/input services
have different assumptions. Choose one coherent model for a port and document
where it crosses the boundary. Raw MMIO addresses remain private implementation
detail; use these helpers rather than copying register constants.
