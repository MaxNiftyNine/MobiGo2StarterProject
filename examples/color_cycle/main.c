/* Minimal MobiGo 2 framebuffer demo: cycle a full-screen RGB565 color.
 *
 * This intentionally long-running hardware example uses the maintained
 * low-level SDK surface.  Resident-lifecycle applications should use the
 * normal SY starter and standard controls instead.
 */

#include "mobigo_sdk/direct_controls.h"

int main(void)
{
    struct mg_sdk_framebuffers framebuffers;
    struct mg_sdk_direct_controls controls;
    mg_sdk_u16 color;
    mg_sdk_u16 color_index = 0;
    mg_sdk_u16 hold;
    volatile mg_sdk_u16 delay;

    mg_sdk_watchdog_kick();
    (void)mg_sdk_direct_controls_init(&controls);
    if (mg_sdk_framebuffers_capture(&framebuffers) == 0) {
        for (;;) {
            mg_sdk_watchdog_kick();
        }
    }

    /* Returning from this launch routine tells LD that the application has
     * exited. Stay resident, leave IRQ/FIQ enabled, and service the watchdog. */
    for (;;) {
        mg_sdk_watchdog_kick();
        if (color_index == 0U) color = 0xf800;
        else if (color_index == 1U) color = 0x07e0;
        else if (color_index == 2U) color = 0x001f;
        else if (color_index == 3U) color = 0xffe0;
        else if (color_index == 4U) color = 0x07ff;
        else if (color_index == 5U) color = 0xf81f;
        else if (color_index == 6U) color = 0xffff;
        else color = 0x0000;

        (void)mg_sdk_dma_fill_words(
            0,
            color,
            framebuffers.front_word_address,
            MG_SDK_LCD_FRAME_WORDS);
        if (framebuffers.back_word_address !=
            framebuffers.front_word_address) {
            (void)mg_sdk_dma_fill_words(
                0,
                color,
                framebuffers.back_word_address,
                MG_SDK_LCD_FRAME_WORDS);
        }

        for (hold = 0; hold < 1800U; ++hold) {
            mg_sdk_framebuffer_present(framebuffers.front_word_address);
            mg_sdk_watchdog_kick();
            if ((hold & 15U) == 0) {
                mg_sdk_direct_controls_poll(&controls);
            }
            for (delay = 0; delay < 1000U; ++delay) {
            }
        }
        color_index = (mg_sdk_u16)((color_index + 1U) & 7U);
    }
}
