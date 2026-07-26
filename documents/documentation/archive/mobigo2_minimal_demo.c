/*
 * Minimal source-derived MobiGo 2 emulator demo.
 *
 * This is intentionally toolchain-neutral. Adapt MG2_REG16 and MG2_WORD_PTR
 * in mobigo2_hw.h to the unSP compiler/linker being used. The framebuffer
 * address must match the linker script and must be 16-word aligned.
 */

#include "mobigo2_hw.h"

#define DEMO_FB_WORD_ADDRESS 0x080000UL

static volatile unsigned short *const demo_fb =
    MG2_WORD_PTR(DEMO_FB_WORD_ADDRESS);

static int clampi(int value, int low, int high)
{
    if (value < low) return low;
    if (value > high) return high;
    return value;
}

static int touch_raw_to_x(unsigned raw)
{
    const int xmin = 0x0186;
    const int xmax = 0x0e80;
    return clampi((xmax - (int)raw) * 319 / (xmax - xmin), 0, 319);
}

static int touch_raw_to_y(unsigned raw)
{
    const int ymin = 0x02b6;
    const int ymax = 0x0d5c;
    return clampi(((int)raw - ymin) * 239 / (ymax - ymin), 0, 239);
}

static int touch_contact(void)
{
    MG2_GPIO_ATTR(MG2_GPIO_E) |= 0x0400;
    MG2_GPIO_DIR(MG2_GPIO_E)  |= 0x0400;
    MG2_GPIO_DATA(MG2_GPIO_E) |= 0x0400;
    return (MG2_GPIO_DATA(MG2_GPIO_E) & 0x0100) != 0;
}

static void draw_dot(int cx, int cy, unsigned short color)
{
    int dx, dy;
    for (dy = -2; dy <= 2; ++dy) {
        for (dx = -2; dx <= 2; ++dx) {
            int x = cx + dx;
            int y = cy + dy;
            if (x >= 0 && x < (int)MG2_SCREEN_W &&
                y >= 0 && y < (int)MG2_SCREEN_H) {
                demo_fb[(unsigned long)y * MG2_SCREEN_W + (unsigned)x] = color;
            }
        }
    }
}

int main(void)
{
    unsigned long i;

    for (i = 0; i < MG2_FRAME_WORDS; ++i)
        demo_fb[i] = mg2_rgb565(24, 32, 56);

    mg2_video_init_framebuffer(DEMO_FB_WORD_ADDRESS);

    for (;;) {
        if (touch_contact()) {
            unsigned raw_x = mg2_adc_read12(MG2_ADC_TOUCH_X_CH);
            unsigned raw_y = mg2_adc_read12(MG2_ADC_TOUCH_Y_CH);
            draw_dot(touch_raw_to_x(raw_x), touch_raw_to_y(raw_y),
                     mg2_rgb565(255, 220, 32));
        }
    }
}
