/* Minimal MobiGo 2 SY hardware demo: cycle a full-screen RGB565 color.
 *
 * This bare MBA intentionally bypasses the compiler's normal C startup. Keep
 * everything in one function and use no initialized global/static data.
 */

#define REG16(address) (*(volatile unsigned short *)(address))
#define DMA_COLOR_WORD 0x6000
#define FRAMEBUFFER_WORDS 0x12c00UL

/* The build replaces the first 12 words at the MBA entry with its hardware
 * startup stub. Keep this public function first so that replacement never
 * overwrites main(). */
void mba_entry_reserve(void)
{
    REG16(0x780b) = 0xa005;
    REG16(0x780a) = 0x0000;
    REG16(0x780b) = 0xa005;
    REG16(0x780a) = 0x0000;
}

/* Use the GPL16250VA DMA sequence from Generalplus's own SDK. Framebuffers
 * can sit above the CPU's directly addressable 22-bit range, so the split
 * high/low DMA address registers are required. */
void fill_physical_buffer(unsigned short low, unsigned short high,
                          unsigned short color)
{
    unsigned long timeout;

    REG16(DMA_COLOR_WORD) = color;
    REG16(0x7a80) = 0x0200; /* C_DMA_SoftReset */
    REG16(0x7abf) = 0x0001; /* clear old DMA0 completion, write-one-to-clear */
    REG16(0x7a81) = DMA_COLOR_WORD;
    REG16(0x7a84) = 0x0000;
    REG16(0x7a82) = low & 0xfff0;
    REG16(0x7a85) = high & 0x07ff;
    REG16(0x7a83) = (unsigned short)(FRAMEBUFFER_WORDS & 0xffffUL);
    REG16(0x7a86) = (unsigned short)(FRAMEBUFFER_WORDS >> 16);

    /* Source fixed + normal interrupt mode + software start. The previous
     * build omitted C_NormalIntMode (0x0008), which is not the SDK sequence. */
    REG16(0x7a80) = 0x0089;
    timeout = 0x000fffffUL;
    while (!(REG16(0x7abf) & 0x0001) && timeout != 0) {
        --timeout;
        REG16(0x780b) = 0xa005;
    }
    REG16(0x7abf) = 0x0001;
}

int main(void)
{
    unsigned short color;
    unsigned short color_index = 0;
    unsigned short hold;
    volatile unsigned short delay;
    unsigned short fbi_low;
    unsigned short fbi_high;
    unsigned short fbo_low;
    unsigned short fbo_high;

    /* Leave IRQ and FIQ enabled. The earlier entry stub issued INT OFF, which
     * stopped the real unit's display/OS servicing even though Emulator2 kept
     * presenting the framebuffer. */
    REG16(0x780b) = 0xa005;

    /* The retail launcher owns SDRAM allocation. Capture its active buffers
     * instead of assuming an emulator-specific physical address. */
    fbi_low = REG16(0x7078);
    fbi_high = REG16(0x7079);
    fbo_low = REG16(0x707a);
    fbo_high = REG16(0x707b);

    /* Returning from this launch routine tells LD that the application has
     * exited. Stay resident, but keep interrupts enabled and service the
     * watchdog so the retail hardware services continue running. */
    for (;;) {
        REG16(0x780b) = 0xa005;
        if (color_index == 0U) color = 0xf800;
        else if (color_index == 1U) color = 0x07e0;
        else if (color_index == 2U) color = 0x001f;
        else if (color_index == 3U) color = 0xffe0;
        else if (color_index == 4U) color = 0x07ff;
        else if (color_index == 5U) color = 0xf81f;
        else if (color_index == 6U) color = 0xffff;
        else color = 0x0000;

        fill_physical_buffer(fbi_low, fbi_high, color);
        if ((fbo_low != fbi_low) || (fbo_high != fbi_high)) {
            fill_physical_buffer(fbo_low, fbo_high, color);
        }

        /* Hold each color while keeping scanout asserted. IRQ/FIQ remain
         * enabled throughout both loops. */
        for (hold = 0; hold < 1800U; ++hold) {
            REG16(0x7078) = fbi_low & 0xfff0;
            REG16(0x7079) = fbi_high & 0x07ff;
            REG16(0x707a) = fbi_low & 0xfff0;
            REG16(0x707b) = fbi_high & 0x07ff;
            REG16(0x707f) = 0x0088;
            REG16(0x780b) = 0xa005;
            for (delay = 0; delay < 1000U; ++delay) { }
        }

        color_index = (color_index + 1U) & 7U;
    }
}
