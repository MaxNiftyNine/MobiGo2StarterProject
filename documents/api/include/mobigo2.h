#ifndef MOBIGO2_API_H
#define MOBIGO2_API_H

/* Source-derived MobiGo 2 API for the supplied emulator.
 * All addresses are 16-bit WORD addresses. This is a freestanding API. */

#ifdef __cplusplus
extern "C" {
#endif

typedef unsigned char  mg2_u8;
typedef signed char    mg2_s8;
typedef unsigned short mg2_u16;
typedef signed short   mg2_s16;

typedef struct { mg2_u16 lo, hi; } mg2_addr22;
typedef struct { mg2_u16 pressed, x, y, raw_x, raw_y; } mg2_touch;
typedef struct { mg2_u16 x, y, width, height; } mg2_rect;

#define MG2_SCREEN_WIDTH  320
#define MG2_SCREEN_HEIGHT 240
#define MG2_FRAME_WORDS   76800
#define MG2_ADDR(lo_, hi_) ((mg2_addr22){(mg2_u16)(lo_), (mg2_u16)((hi_) & 0x003f)})
#define MG2_REG16(a) (*(volatile mg2_u16 *)(a))

enum mg2_result { MG2_OK = 0, MG2_ERROR = 1, MG2_TIMEOUT = 2, MG2_UNSUPPORTED = 3 };
enum mg2_gpio_port { MG2_GPIO_A, MG2_GPIO_B, MG2_GPIO_C, MG2_GPIO_D, MG2_GPIO_E };
enum mg2_timer { MG2_TIMER_A, MG2_TIMER_B, MG2_TIMER_C, MG2_TIMER_D };
enum mg2_layer { MG2_LAYER_0, MG2_LAYER_1, MG2_LAYER_2, MG2_LAYER_3 };

enum {
    MG2_PPU_ENABLE = 0x0001, MG2_PPU_TILE0_TRANSPARENT = 0x0002,
    MG2_PPU_EXTENDED_CHARACTER = 0x0004, MG2_PPU_REVERSE_LAYERS = 0x0008,
    MG2_PPU_FREE_ADDRESS = 0x0040, MG2_PPU_FRAME_BASE = 0x0080,
    MG2_PPU_OUTPUT_RGB555 = 0x0100, MG2_PPU_SPRITE_EXT_LAYOUT = 0x0200
};
enum {
    MG2_LAYER_LINEMAP = 0x0001, MG2_LAYER_GLOBAL_ATTRIBUTES = 0x0002,
    MG2_LAYER_FIXED_TILE = 0x0004, MG2_LAYER_ENABLE = 0x0008,
    MG2_LAYER_ROW_SCROLL = 0x0010, MG2_LAYER_VERTICAL_COMPRESS = 0x0040,
    MG2_LAYER_DIRECT_COLOR = 0x0080, MG2_LAYER_BLEND = 0x0100
};
enum { MG2_DMA_IRQ = 0x0100, MG2_DMA_RESET = 0x0200,
       MG2_DMA_SOURCE_BYTE = 0x1000, MG2_DMA_DEST_BYTE = 0x2000 };

typedef struct {
    mg2_addr22 graphics;
    mg2_u16 x_scroll, y_scroll, attributes, control;
    mg2_u16 tilemap, attribute_map;
} mg2_layer_config;

/* Core and memory */
void mg2_init(void);
mg2_u16 mg2_read16(mg2_u16 address_low, mg2_u16 address_high);
void mg2_write16(mg2_u16 address_low, mg2_u16 address_high, mg2_u16 value);
mg2_u16 mg2_random_status(void);

/* Color and framebuffer drawing */
mg2_u16 mg2_rgb565(mg2_u16 red, mg2_u16 green, mg2_u16 blue);
mg2_u16 mg2_rgb555(mg2_u16 red, mg2_u16 green, mg2_u16 blue);
void mg2_video_timing_default(void);
void mg2_video_set_input(mg2_u16 address_low, mg2_u16 address_high);
void mg2_video_set_output(mg2_u16 address_low, mg2_u16 address_high);
void mg2_video_framebuffer_init(mg2_u16 address_low, mg2_u16 address_high);
void mg2_video_enable(mg2_u16 flags);
mg2_u16 mg2_video_scanline(void);
mg2_u16 mg2_video_irq_status(void);
void mg2_video_irq_enable(mg2_u16 mask);
void mg2_video_irq_ack(mg2_u16 mask);
enum mg2_result mg2_video_wait_frame(mg2_u16 timeout);
enum mg2_result mg2_video_composite(mg2_u16 timeout);
void mg2_draw_target(mg2_u16 address_low, mg2_u16 address_high);
void mg2_draw_pixel(mg2_s16 x, mg2_s16 y, mg2_u16 color);
mg2_u16 mg2_draw_read_pixel(mg2_s16 x, mg2_s16 y);
void mg2_draw_fill(mg2_u16 color);
void mg2_draw_rect(mg2_u16 x, mg2_u16 y, mg2_u16 width, mg2_u16 height, mg2_u16 color);

/* PPU, palette, layers, sprites, local video DMA */
void mg2_palette_write(mg2_u16 index, mg2_u16 rgb555);
mg2_u16 mg2_palette_read(mg2_u16 index);
void mg2_layer_configure(enum mg2_layer layer, mg2_u16 gfx_low, mg2_u16 gfx_high,
                         mg2_u16 x, mg2_u16 y, mg2_u16 attributes, mg2_u16 control,
                         mg2_u16 tilemap, mg2_u16 attribute_map);
void mg2_layer_scroll(enum mg2_layer layer, mg2_s16 x, mg2_s16 y);
void mg2_row_scroll_write(mg2_u16 line, mg2_s16 offset);
void mg2_sprite_enable(mg2_u16 count, mg2_u16 direct_coordinates);
void mg2_sprite_write(mg2_u16 index, mg2_u16 tile, mg2_s16 x, mg2_s16 y, mg2_u16 attributes);
void mg2_sprite_disable(mg2_u16 index);
void mg2_video_dma_copy(mg2_u16 source, mg2_u16 destination, mg2_u16 words);

/* GPIO, keyboard matrix, ADC and touch */
mg2_u16 mg2_gpio_read(enum mg2_gpio_port port);
mg2_u16 mg2_gpio_latch(enum mg2_gpio_port port);
void mg2_gpio_write(enum mg2_gpio_port port, mg2_u16 value);
void mg2_gpio_set_output(enum mg2_gpio_port port, mg2_u16 mask, mg2_u16 non_inverted);
void mg2_gpio_set_input(enum mg2_gpio_port port, mg2_u16 mask);
mg2_u16 mg2_matrix_scan_row(mg2_u16 row);
mg2_u16 mg2_matrix_scan_all(mg2_u16 rows[6]);
mg2_u16 mg2_adc_read12(mg2_u16 channel);
mg2_u16 mg2_battery_read(void);
mg2_u16 mg2_touch_contact(void);

/* DMA and interrupt controller */
void mg2_dma_copy(mg2_u16 channel, mg2_u16 source_low, mg2_u16 source_high,
                  mg2_u16 destination_low, mg2_u16 destination_high,
                  mg2_u16 count_low, mg2_u16 count_high, mg2_u16 flags);
mg2_u16 mg2_dma_status(void);
void mg2_dma_ack(mg2_u16 mask);
mg2_u16 mg2_irq_status1(void);
mg2_u16 mg2_irq_status2(void);
void mg2_irq_ack1(mg2_u16 mask);
void mg2_irq_ack2(mg2_u16 mask);
void mg2_irq_set_routing(mg2_u16 priority1, mg2_u16 priority2);

/* Timers, timebases, RTC and clocks */
void mg2_timer_start(enum mg2_timer timer, mg2_u16 preload, mg2_u16 source_a,
                     mg2_u16 source_b, mg2_u16 irq_enable);
void mg2_timer_stop(enum mg2_timer timer);
mg2_u16 mg2_timer_count(enum mg2_timer timer);
mg2_u16 mg2_timer_overflowed(enum mg2_timer timer);
void mg2_timer_ack(enum mg2_timer timer);
void mg2_timebase_start(mg2_u16 unit, mg2_u16 rate, mg2_u16 irq_enable);
void mg2_timebase_stop(mg2_u16 unit);
void mg2_timebase_ack(mg2_u16 unit);
void mg2_rtc_scheduler_start(mg2_u16 rate, mg2_u16 irq_enable);
void mg2_rtc_scheduler_stop(void);
mg2_u16 mg2_rtc_status(void);
void mg2_rtc_ack(mg2_u16 mask);
mg2_u16 mg2_clock_control(void);
mg2_u16 mg2_pll_multiplier(void);

/* Watchdog and power. Sleep/reset deliberately change execution state. */
void mg2_watchdog_start(mg2_u16 timeout_selector, mg2_u16 cpu_only);
void mg2_watchdog_stop(void);
void mg2_watchdog_feed(void);
mg2_u16 mg2_reset_cause(void);
void mg2_reset_cause_ack(mg2_u16 mask);
void mg2_request_sleep(void);

/* SPI NOR */
void mg2_spi_init(void);
void mg2_spi_select(mg2_u16 active);
mg2_u8 mg2_spi_transfer(mg2_u8 value);
mg2_u8 mg2_spi_read_byte(mg2_u8 a2, mg2_u8 a1, mg2_u8 a0);
void mg2_spi_jedec_id(mg2_u8 id[3]);
mg2_u8 mg2_spi_status(void);

/* NAND. Low-level commands are provided; program/erase modify the image. */
mg2_u16 mg2_nand_ready(void);
void mg2_nand_command(mg2_u8 command);
void mg2_nand_set_address(mg2_u16 column, mg2_u16 page);
mg2_u8 mg2_nand_data_read(void);
void mg2_nand_data_write(mg2_u8 value);
void mg2_nand_read_id(mg2_u8 id[2]);
mg2_u8 mg2_nand_read_byte(mg2_u16 page, mg2_u16 column);
void mg2_nand_program_byte(mg2_u16 page, mg2_u16 column, mg2_u8 value);
void mg2_nand_erase_block(mg2_u16 page_in_block);

/* Audio FIFO and partially modeled peripherals */
void mg2_audio_fifo_reset(mg2_u16 channel);
void mg2_audio_fifo_write(mg2_u16 channel, mg2_u16 sample);
mg2_u16 mg2_audio_fifo_level(mg2_u16 channel);
mg2_u16 mg2_audio_fifo_full(mg2_u16 channel);
void mg2_audio_dac_control(mg2_u16 value);
void mg2_cache_flush(void);
void mg2_usb_enable(mg2_u16 enable);
mg2_u16 mg2_usb_status(void);
void mg2_usb_ack(mg2_u16 mask);
mg2_u16 mg2_sd2_read(mg2_u16 offset);
void mg2_sd2_write(mg2_u16 offset, mg2_u16 value);

#ifdef __cplusplus
}
#endif
#endif
