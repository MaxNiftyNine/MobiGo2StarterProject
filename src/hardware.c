#include "mobigo_sdk/hardware.h"
#include "mobigo_sdk/memory_map.h"

/*
 * Verified GPL16250/MobiGo 2 registers.  Raw addresses deliberately remain
 * private so applications share one reviewed implementation.
 */
#if defined(_WIN64)
typedef unsigned long long mg_sdk_hw_pointer_uint;
#else
typedef unsigned long mg_sdk_hw_pointer_uint;
#endif

#define HW_REG16(address) \
    (*(volatile mg_sdk_u16 *)(mg_sdk_hw_pointer_uint)(address))

enum {
    HW_WATCHDOG_CLEAR = 0x780b,
    HW_PPU_IRQ_ENABLE = 0x7062,
    HW_PPU_IRQ_STATUS = 0x7063,
    HW_FRAMEBUFFER_IN_LOW = 0x7078,
    HW_FRAMEBUFFER_IN_HIGH = 0x7079,
    HW_FRAMEBUFFER_OUT_LOW = 0x707a,
    HW_FRAMEBUFFER_OUT_HIGH = 0x707b,
    HW_PPU_MODE = 0x707f,
    HW_DMA_BASE = 0x7a80,
    HW_DMA_COMPLETE = 0x7abf,
    HW_GPIO_A_DATA = 0x7860,
    HW_GPIO_A_FUNCTION = 0x7862,
    HW_GPIO_B_DATA = 0x7868,
    HW_GPIO_B_FUNCTION = 0x786a,
    HW_GPIO_C_DATA = 0x7870,
    HW_GPIO_C_DIRECTION = 0x7872,
    HW_GPIO_C_ATTRIBUTE = 0x7873,
    HW_GPIO_E_DATA = 0x7880,
    HW_GPIO_E_DIRECTION = 0x7882,
    HW_GPIO_E_ATTRIBUTE = 0x7883
};

#define HW_ADDRESS_LIMIT ((mg_sdk_u32)0x07ffffffUL)
#define HW_DMA_COPY_CONTROL ((mg_sdk_u16)0x0009u)
#define HW_DMA_FILL_CONTROL ((mg_sdk_u16)0x0089u)

static mg_sdk_u32 hw_join_address(mg_sdk_u16 low, mg_sdk_u16 high)
{
    return (mg_sdk_u32)low | ((mg_sdk_u32)(high & 0x07ffu) << 16);
}

static int hw_framebuffer_address_valid(mg_sdk_u32 word_address)
{
    return word_address != 0 && word_address <= HW_ADDRESS_LIMIT &&
        (word_address & 0x000fu) == 0;
}

static void hw_write_address(
    mg_sdk_u32 address,
    unsigned long low_register,
    unsigned long high_register,
    int align_low)
{
    mg_sdk_u16 low = (mg_sdk_u16)(address & 0xffffUL);
    if (align_low != 0) {
        low &= 0xfff0u;
    }
    HW_REG16(low_register) = low;
    HW_REG16(high_register) = (mg_sdk_u16)((address >> 16) & 0x07ffUL);
}

void mg_sdk_watchdog_kick(void)
{
    HW_REG16(HW_WATCHDOG_CLEAR) = 0xa005u;
}

int mg_sdk_framebuffers_capture(struct mg_sdk_framebuffers *framebuffers)
{
    if (framebuffers == 0) {
        return 0;
    }
    framebuffers->front_word_address = hw_join_address(
        HW_REG16(HW_FRAMEBUFFER_IN_LOW),
        HW_REG16(HW_FRAMEBUFFER_IN_HIGH));
    framebuffers->back_word_address = hw_join_address(
        HW_REG16(HW_FRAMEBUFFER_OUT_LOW),
        HW_REG16(HW_FRAMEBUFFER_OUT_HIGH));
    framebuffers->width = MG_SDK_LCD_WIDTH;
    framebuffers->height = MG_SDK_LCD_HEIGHT;
    framebuffers->stride_words = MG_SDK_LCD_STRIDE_WORDS;
    return framebuffers->front_word_address != 0 &&
        framebuffers->back_word_address != 0;
}

void mg_sdk_framebuffer_present(mg_sdk_u32 word_address)
{
    if (!hw_framebuffer_address_valid(word_address)) {
        return;
    }
    hw_write_address(
        word_address, HW_FRAMEBUFFER_IN_LOW, HW_FRAMEBUFFER_IN_HIGH, 1);
    hw_write_address(
        word_address, HW_FRAMEBUFFER_OUT_LOW, HW_FRAMEBUFFER_OUT_HIGH, 1);
    HW_REG16(HW_PPU_MODE) = 0x0088u;
}

void mg_sdk_framebuffer_take_ownership(mg_sdk_u32 word_address)
{
    if (!hw_framebuffer_address_valid(word_address)) {
        return;
    }
    HW_REG16(HW_PPU_IRQ_ENABLE) = 0;
    HW_REG16(HW_PPU_IRQ_STATUS) = 0xffffu;
    mg_sdk_framebuffer_present(word_address);
}

int mg_sdk_dma_start(
    mg_sdk_u16 channel,
    mg_sdk_u32 source_word_address,
    mg_sdk_u32 destination_word_address,
    mg_sdk_u32 word_count,
    enum mg_sdk_dma_mode mode)
{
    unsigned long base;
    mg_sdk_u16 flag;
    mg_sdk_u16 control;

    if (channel >= MG_SDK_DMA_CHANNELS || word_count == 0 ||
        source_word_address > HW_ADDRESS_LIMIT ||
        destination_word_address > HW_ADDRESS_LIMIT ||
        (destination_word_address & 0x000fu) != 0 ||
        (mode != MG_SDK_DMA_MODE_COPY &&
         mode != MG_SDK_DMA_MODE_FIXED_SOURCE)) {
        return MG_SDK_DMA_INVALID_ARGUMENT;
    }
    if (word_count - 1UL >
        HW_ADDRESS_LIMIT - destination_word_address) {
        return MG_SDK_DMA_INVALID_ARGUMENT;
    }
    if (mode == MG_SDK_DMA_MODE_COPY &&
        word_count - 1UL > HW_ADDRESS_LIMIT - source_word_address) {
        return MG_SDK_DMA_INVALID_ARGUMENT;
    }
    control = mode == MG_SDK_DMA_MODE_FIXED_SOURCE
        ? HW_DMA_FILL_CONTROL
        : HW_DMA_COPY_CONTROL;

    base = (unsigned long)HW_DMA_BASE + (unsigned long)channel * 8UL;
    flag = (mg_sdk_u16)(1u << channel);
    HW_REG16(base) = 0x0200u;
    HW_REG16(HW_DMA_COMPLETE) = flag;
    hw_write_address(source_word_address, base + 1UL, base + 4UL, 0);
    hw_write_address(destination_word_address, base + 2UL, base + 5UL, 1);
    HW_REG16(base + 3UL) = (mg_sdk_u16)(word_count & 0xffffUL);
    HW_REG16(base + 6UL) =
        (mg_sdk_u16)((word_count >> 16) & 0x07ffUL);
    HW_REG16(base) = control;
    return MG_SDK_DMA_OK;
}

int mg_sdk_dma_wait(mg_sdk_u16 channel, mg_sdk_u32 timeout)
{
    mg_sdk_u16 flag;
    if (channel >= MG_SDK_DMA_CHANNELS || timeout == 0) {
        return MG_SDK_DMA_INVALID_ARGUMENT;
    }
    flag = (mg_sdk_u16)(1u << channel);
    while ((HW_REG16(HW_DMA_COMPLETE) & flag) == 0) {
        --timeout;
        if ((timeout & 0x0fffUL) == 0) {
            mg_sdk_watchdog_kick();
        }
        if (timeout == 0) {
            unsigned long base =
                (unsigned long)HW_DMA_BASE + (unsigned long)channel * 8UL;
            HW_REG16(base) = 0x0200u;
            HW_REG16(HW_DMA_COMPLETE) = flag;
            return MG_SDK_DMA_TIMEOUT;
        }
    }
    HW_REG16(HW_DMA_COMPLETE) = flag;
    return MG_SDK_DMA_OK;
}

int mg_sdk_dma_copy_words(
    mg_sdk_u16 channel,
    mg_sdk_u32 source_word_address,
    mg_sdk_u32 destination_word_address,
    mg_sdk_u32 word_count)
{
    int result = mg_sdk_dma_start(
        channel,
        source_word_address,
        destination_word_address,
        word_count,
        MG_SDK_DMA_MODE_COPY);
    if (result != MG_SDK_DMA_OK) {
        return result;
    }
    return mg_sdk_dma_wait(channel, MG_SDK_DMA_DEFAULT_TIMEOUT);
}

int mg_sdk_dma_fill_words(
    mg_sdk_u16 channel,
    mg_sdk_u16 value,
    mg_sdk_u32 destination_word_address,
    mg_sdk_u32 word_count)
{
    int result;
    if (channel >= MG_SDK_DMA_CHANNELS || word_count == 0 ||
        destination_word_address > HW_ADDRESS_LIMIT ||
        (destination_word_address & 0x000fu) != 0 ||
        word_count - 1UL >
            HW_ADDRESS_LIMIT - destination_word_address) {
        return MG_SDK_DMA_INVALID_ARGUMENT;
    }
    HW_REG16(MG_SDK_HARDWARE_SCRATCH_WORD_ADDRESS) = value;
    result = mg_sdk_dma_start(
        channel,
        (mg_sdk_u32)MG_SDK_HARDWARE_SCRATCH_WORD_ADDRESS,
        destination_word_address,
        word_count,
        MG_SDK_DMA_MODE_FIXED_SOURCE);
    if (result != MG_SDK_DMA_OK) {
        return result;
    }
    return mg_sdk_dma_wait(channel, MG_SDK_DMA_DEFAULT_TIMEOUT);
}

static void hw_matrix_deactivate_rows(void)
{
    HW_REG16(HW_GPIO_C_DATA) &= (mg_sdk_u16)~0x06e0u;
    HW_REG16(HW_GPIO_E_DATA) &= (mg_sdk_u16)~0x0004u;
}

static mg_sdk_u16 hw_matrix_read_columns(void)
{
    mg_sdk_u16 port_b = HW_REG16(HW_GPIO_B_DATA);
    mg_sdk_u16 port_a = HW_REG16(HW_GPIO_A_DATA);
    return (mg_sdk_u16)(((port_b >> 10) & 0x003fu) |
        ((port_a >> 5) & 0x01c0u));
}

void mg_sdk_matrix_init(void)
{
    HW_REG16(HW_GPIO_A_FUNCTION) &= (mg_sdk_u16)~0x3800u;
    HW_REG16(HW_GPIO_B_FUNCTION) &= (mg_sdk_u16)~0xfc00u;
    hw_matrix_deactivate_rows();
}

mg_sdk_u16 mg_sdk_matrix_scan_row(mg_sdk_u16 row)
{
    volatile mg_sdk_u16 settle;
    mg_sdk_u16 bit;

    if (row >= MG_SDK_MATRIX_ROWS) {
        return 0;
    }
    hw_matrix_deactivate_rows();
    if (row == 0) {
        bit = 0x0080u;
    } else if (row == 1) {
        bit = 0x0040u;
    } else if (row == 2) {
        bit = 0x0400u;
    } else if (row == 3) {
        bit = 0x0200u;
    } else if (row == 4) {
        bit = 0x0020u;
    } else {
        bit = 0;
    }
    if (row < 5) {
        HW_REG16(HW_GPIO_C_ATTRIBUTE) |= bit;
        HW_REG16(HW_GPIO_C_DIRECTION) |= bit;
        HW_REG16(HW_GPIO_C_DATA) |= bit;
    } else {
        HW_REG16(HW_GPIO_E_ATTRIBUTE) |= 0x0004u;
        HW_REG16(HW_GPIO_E_DIRECTION) |= 0x0004u;
        HW_REG16(HW_GPIO_E_DATA) |= 0x0004u;
    }
    for (settle = 0; settle < 16u; ++settle) {
    }
    bit = hw_matrix_read_columns();
    hw_matrix_deactivate_rows();
    return bit;
}

void mg_sdk_matrix_scan(struct mg_sdk_matrix_state *state)
{
    mg_sdk_u16 row;
    if (state == 0) {
        return;
    }
    for (row = 0; row < MG_SDK_MATRIX_ROWS; ++row) {
        state->row[row] = mg_sdk_matrix_scan_row(row);
    }
}

int mg_sdk_matrix_cell_down(
    const struct mg_sdk_matrix_state *state,
    mg_sdk_u16 row,
    mg_sdk_u16 column)
{
    if (state == 0 || row >= MG_SDK_MATRIX_ROWS ||
        column >= MG_SDK_MATRIX_COLUMNS) {
        return 0;
    }
    return (state->row[row] & (mg_sdk_u16)(1u << column)) != 0;
}

mg_sdk_u16 mg_sdk_matrix_game_keys(
    const struct mg_sdk_matrix_state *state)
{
    mg_sdk_u16 keys = 0;
    if (mg_sdk_matrix_cell_down(state, 3, 4)) keys |= MG_SDK_GAME_KEY_UP;
    if (mg_sdk_matrix_cell_down(state, 4, 4)) keys |= MG_SDK_GAME_KEY_DOWN;
    if (mg_sdk_matrix_cell_down(state, 3, 3)) keys |= MG_SDK_GAME_KEY_LEFT;
    if (mg_sdk_matrix_cell_down(state, 4, 3)) keys |= MG_SDK_GAME_KEY_RIGHT;
    if (mg_sdk_matrix_cell_down(state, 3, 5)) keys |= MG_SDK_GAME_KEY_PRIMARY;
    if (mg_sdk_matrix_cell_down(state, 4, 2)) keys |= MG_SDK_GAME_KEY_EXIT;
    if (mg_sdk_matrix_cell_down(state, 4, 5)) keys |= MG_SDK_GAME_KEY_HELP;
    return keys;
}

mg_sdk_u16 mg_sdk_matrix_system_keys(
    const struct mg_sdk_matrix_state *state)
{
    mg_sdk_u16 keys = 0;
    if (mg_sdk_matrix_cell_down(state, 3, 2)) keys |= MG_SDK_KEY_OFF;
    if (mg_sdk_matrix_cell_down(state, 4, 7)) keys |= MG_SDK_KEY_VOLUME_DOWN;
    if (mg_sdk_matrix_cell_down(state, 4, 8)) keys |= MG_SDK_KEY_VOLUME_UP;
    if (mg_sdk_matrix_cell_down(state, 4, 6)) keys |= MG_SDK_KEY_BRIGHTNESS;
    return keys;
}
