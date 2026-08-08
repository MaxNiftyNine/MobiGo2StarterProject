#include <assert.h>
#include <string.h>

#include "mobigo_sdk/hardware.h"

int main(void)
{
    struct mg_sdk_matrix_state state;
    mg_sdk_u16 game;
    mg_sdk_u16 system;

    memset(&state, 0, sizeof(state));
    state.row[3] = (mg_sdk_u16)(
        (1u << 2) | (1u << 3) | (1u << 4) | (1u << 5));
    state.row[4] = (mg_sdk_u16)(
        (1u << 2) | (1u << 3) | (1u << 4) | (1u << 5) |
        (1u << 6) | (1u << 7) | (1u << 8));

    game = mg_sdk_matrix_game_keys(&state);
    assert((game & MG_SDK_GAME_KEY_UP) != 0);
    assert((game & MG_SDK_GAME_KEY_DOWN) != 0);
    assert((game & MG_SDK_GAME_KEY_LEFT) != 0);
    assert((game & MG_SDK_GAME_KEY_RIGHT) != 0);
    assert((game & MG_SDK_GAME_KEY_PRIMARY) != 0);
    assert((game & MG_SDK_GAME_KEY_EXIT) != 0);
    assert((game & MG_SDK_GAME_KEY_HELP) != 0);

    system = mg_sdk_matrix_system_keys(&state);
    assert((system & MG_SDK_KEY_OFF) != 0);
    assert((system & MG_SDK_KEY_VOLUME_DOWN) != 0);
    assert((system & MG_SDK_KEY_VOLUME_UP) != 0);
    assert((system & MG_SDK_KEY_BRIGHTNESS) != 0);

    assert(mg_sdk_matrix_cell_down(&state, 3, 5));
    assert(!mg_sdk_matrix_cell_down(&state, 0, 0));
    assert(!mg_sdk_matrix_cell_down(&state, MG_SDK_MATRIX_ROWS, 0));
    assert(!mg_sdk_matrix_cell_down(&state, 0, MG_SDK_MATRIX_COLUMNS));
    assert(!mg_sdk_matrix_cell_down(0, 0, 0));

    /* Invalid calls are rejected before target MMIO is touched, so boundary
     * and overflow validation remains host-testable. */
    assert(!mg_sdk_framebuffers_capture(0));
    mg_sdk_framebuffer_present(0);
    assert(mg_sdk_dma_start(
        MG_SDK_DMA_CHANNELS, 0, 0x10, 1, MG_SDK_DMA_MODE_COPY) ==
        MG_SDK_DMA_INVALID_ARGUMENT);
    assert(mg_sdk_dma_start(
        0, 0, 0x11, 1, MG_SDK_DMA_MODE_COPY) ==
        MG_SDK_DMA_INVALID_ARGUMENT);
    assert(mg_sdk_dma_start(
        0, 0x07fffff0UL, 0x10, 0x20,
        MG_SDK_DMA_MODE_COPY) == MG_SDK_DMA_INVALID_ARGUMENT);
    assert(mg_sdk_dma_start(
        0, 0x10, 0x07fffff0UL, 0x20,
        MG_SDK_DMA_MODE_COPY) == MG_SDK_DMA_INVALID_ARGUMENT);
    assert(mg_sdk_dma_start(
        0, 0x10, 0x20, 1, (enum mg_sdk_dma_mode)99) ==
        MG_SDK_DMA_INVALID_ARGUMENT);
    assert(mg_sdk_dma_fill_words(0, 0xffffu, 0x11, 1) ==
        MG_SDK_DMA_INVALID_ARGUMENT);
    assert(mg_sdk_dma_wait(MG_SDK_DMA_CHANNELS, 1) ==
        MG_SDK_DMA_INVALID_ARGUMENT);
    assert(mg_sdk_dma_wait(0, 0) == MG_SDK_DMA_INVALID_ARGUMENT);
    return 0;
}
