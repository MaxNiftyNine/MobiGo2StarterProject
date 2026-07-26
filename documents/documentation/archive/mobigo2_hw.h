#ifndef MOBIGO2_HW_H
#define MOBIGO2_HW_H

/*
 * Source-derived MobiGo 2 / GPL16250-class register helper.
 *
 * IMPORTANT: all numeric addresses in this file are 16-bit WORD addresses.
 * Adapt MG2_REG16 and MG2_WORD_PTR to the target unSP compiler's pointer model.
 */

#ifndef MG2_REG16
#define MG2_REG16(a) (*(volatile unsigned short *)(a))
#endif

#ifndef MG2_WORD_PTR
#define MG2_WORD_PTR(a) ((volatile unsigned short *)(a))
#endif

#define MG2_SCREEN_W        320u
#define MG2_SCREEN_H        240u
#define MG2_FRAME_WORDS     (MG2_SCREEN_W * MG2_SCREEN_H)

/* Video / PPU */
#define MG2_TFT_SCANLINE        MG2_REG16(0x7038)
#define MG2_PALETTE_CTRL        MG2_REG16(0x703a)
#define MG2_SPRITE_CTRL         MG2_REG16(0x7042)
#define MG2_TFT_CTRL            MG2_REG16(0x7050)
#define MG2_TFT_V_WIDTH         MG2_REG16(0x7051)
#define MG2_TFT_FRAME_LINE      MG2_REG16(0x7054)
#define MG2_TFT_H_WIDTH         MG2_REG16(0x7055)
#define MG2_TFT_STATUS          MG2_REG16(0x705a)
#define MG2_VIDEO_IRQ_ENABLE    MG2_REG16(0x7062)
#define MG2_VIDEO_IRQ_STATUS    MG2_REG16(0x7063)
#define MG2_VIDEO_DMA_SOURCE    MG2_REG16(0x7070)
#define MG2_VIDEO_DMA_DEST      MG2_REG16(0x7071)
#define MG2_VIDEO_DMA_SIZE      MG2_REG16(0x7072)
#define MG2_FBI_LOW             MG2_REG16(0x7078)
#define MG2_FBI_HIGH            MG2_REG16(0x7079)
#define MG2_FBO_LOW             MG2_REG16(0x707a)
#define MG2_FBO_HIGH            MG2_REG16(0x707b)
#define MG2_FB_PPU_GO           MG2_REG16(0x707c)
#define MG2_PPU_RAM_BANK        MG2_REG16(0x707e)
#define MG2_PPU_ENABLE          MG2_REG16(0x707f)

#define MG2_PPU_EN              0x0001u
#define MG2_PPU_TILE0_TRANS     0x0002u
#define MG2_PPU_EXT_CHAR        0x0004u
#define MG2_PPU_REVERSE_LAYERS  0x0008u
#define MG2_PPU_FREE_ADDR       0x0040u
#define MG2_PPU_FRAME_BASE      0x0080u
#define MG2_PPU_OUTPUT_RGB555   0x0100u
#define MG2_PPU_SPR_EXT_LAYOUT  0x0200u

#define MG2_VIDEO_FRAME_IRQ     0x0001u
#define MG2_VIDEO_DMA_IRQ       0x0004u
#define MG2_VIDEO_FRAME_ALT     0x0800u

/* GPIO port bases and common offsets. */
#define MG2_GPIO_A 0x7860u
#define MG2_GPIO_B 0x7868u
#define MG2_GPIO_C 0x7870u
#define MG2_GPIO_D 0x7878u
#define MG2_GPIO_E 0x7880u
#define MG2_GPIO_DATA(base) MG2_REG16((base) + 0)
#define MG2_GPIO_BUF(base)  MG2_REG16((base) + 1)
#define MG2_GPIO_DIR(base)  MG2_REG16((base) + 2)
#define MG2_GPIO_ATTR(base) MG2_REG16((base) + 3)

/* Manual ADC. */
#define MG2_MADC_SETUP          MG2_REG16(0x7960)
#define MG2_MADC_CTRL           MG2_REG16(0x7961)
#define MG2_MADC_DATA           MG2_REG16(0x7962)
#define MG2_MADC_START          0x0040u
#define MG2_MADC_READY          0x0080u
#define MG2_MADC_IRQ_ENABLE     0x4000u
#define MG2_MADC_IRQ_FLAG       0x8000u
#define MG2_ADC_BATTERY_CH      0u
#define MG2_ADC_TOUCH_Y_CH      2u
#define MG2_ADC_TOUCH_X_CH      3u

/* Interrupt controller. */
#define MG2_INT_STATUS1         MG2_REG16(0x78a0)
#define MG2_INT_STATUS2         MG2_REG16(0x78a1)
#define MG2_INT_CONTROL0        MG2_REG16(0x78a2)
#define MG2_INT_CONTROL1        MG2_REG16(0x78a3)
#define MG2_INT_PRIORITY1       MG2_REG16(0x78a4)
#define MG2_INT_PRIORITY2       MG2_REG16(0x78a5)

/* Timers. */
#define MG2_TIMER_A_BASE 0x78c0u
#define MG2_TIMER_B_BASE 0x78c8u
#define MG2_TIMER_C_BASE 0x78d0u
#define MG2_TIMER_D_BASE 0x78d8u
#define MG2_TIMER_CTRL(base)    MG2_REG16((base) + 0)
#define MG2_TIMER_PRELOAD(base) MG2_REG16((base) + 2)
#define MG2_TIMER_COUNT(base)   MG2_REG16((base) + 4)
#define MG2_TIMER_ENABLE        0x2000u
#define MG2_TIMER_IRQ_ENABLE    0x4000u
#define MG2_TIMER_FLAG          0x8000u

/* System DMA. */
#define MG2_DMA_BASE(ch)        (0x7a80u + ((ch) * 8u))
#define MG2_DMA_CTRL(ch)        MG2_REG16(MG2_DMA_BASE(ch) + 0)
#define MG2_DMA_SRC_LO(ch)      MG2_REG16(MG2_DMA_BASE(ch) + 1)
#define MG2_DMA_DST_LO(ch)      MG2_REG16(MG2_DMA_BASE(ch) + 2)
#define MG2_DMA_COUNT_LO(ch)    MG2_REG16(MG2_DMA_BASE(ch) + 3)
#define MG2_DMA_SRC_HI(ch)      MG2_REG16(MG2_DMA_BASE(ch) + 4)
#define MG2_DMA_DST_HI(ch)      MG2_REG16(MG2_DMA_BASE(ch) + 5)
#define MG2_DMA_COUNT_HI(ch)    MG2_REG16(MG2_DMA_BASE(ch) + 6)
#define MG2_DMA_STATUS          MG2_REG16(0x7abf)
#define MG2_DMA_ENABLE          0x0001u
#define MG2_DMA_IRQ_ENABLE      0x0100u
#define MG2_DMA_RESET           0x0200u
#define MG2_DMA_SRC_BYTE        0x1000u
#define MG2_DMA_DST_BYTE        0x2000u

/* SPI NOR. */
#define MG2_SPI_CTRL            MG2_REG16(0x7940)
#define MG2_SPI_TX_STATUS       MG2_REG16(0x7941)
#define MG2_SPI_TX              MG2_REG16(0x7942)
#define MG2_SPI_STATUS          MG2_REG16(0x7943)
#define MG2_SPI_RX              MG2_REG16(0x7944)
#define MG2_SPI_MISC            MG2_REG16(0x7945)
#define MG2_SPI_CS_BIT          0x0010u

/* NAND. */
#define MG2_NAND_CTRL           MG2_REG16(0x7850)
#define MG2_NAND_COMMAND        MG2_REG16(0x7851)
#define MG2_NAND_ADDR_LOW       MG2_REG16(0x7852)
#define MG2_NAND_ADDR_HIGH      MG2_REG16(0x7853)
#define MG2_NAND_DATA           MG2_REG16(0x7854)
#define MG2_NAND_DMA_INT        MG2_REG16(0x7855)
#define MG2_NAND_TYPE           MG2_REG16(0x7856)

static unsigned short mg2_rgb565(unsigned r8, unsigned g8, unsigned b8)
{
    return (unsigned short)(((r8 >> 3) << 11) |
                            ((g8 >> 2) << 5) |
                            (b8 >> 3));
}

static unsigned short mg2_rgb555(unsigned r8, unsigned g8, unsigned b8)
{
    return (unsigned short)(((r8 >> 3) << 10) |
                            ((g8 >> 3) << 5) |
                            (b8 >> 3));
}

static void mg2_set_frame_address(volatile unsigned short *low,
                                  volatile unsigned short *high,
                                  unsigned long word_address)
{
    *low = (unsigned short)(word_address & 0xfff0UL);
    *high = (unsigned short)((word_address >> 16) & 0x07ffUL);
}

static void mg2_set_fbi(unsigned long word_address)
{
    MG2_FBI_LOW = (unsigned short)(word_address & 0xfff0UL);
    MG2_FBI_HIGH = (unsigned short)((word_address >> 16) & 0x07ffUL);
}

static void mg2_set_fbo(unsigned long word_address)
{
    MG2_FBO_LOW = (unsigned short)(word_address & 0xfff0UL);
    MG2_FBO_HIGH = (unsigned short)((word_address >> 16) & 0x07ffUL);
}

static void mg2_video_init_framebuffer(unsigned long word_address)
{
    mg2_set_fbi(word_address);
    MG2_PPU_ENABLE = MG2_PPU_EN | MG2_PPU_FRAME_BASE;
}

static void mg2_wait_frame_edge(void)
{
    while ((MG2_VIDEO_IRQ_STATUS & MG2_VIDEO_FRAME_IRQ) == 0)
        ;
    MG2_VIDEO_IRQ_STATUS = MG2_VIDEO_FRAME_IRQ;
}

static unsigned short mg2_adc_read12(unsigned channel)
{
    MG2_MADC_CTRL = MG2_MADC_IRQ_FLAG;
    MG2_MADC_CTRL = (unsigned short)((channel & 7u) | MG2_MADC_START);
    while ((MG2_MADC_CTRL & MG2_MADC_READY) == 0)
        ;
    MG2_MADC_CTRL = MG2_MADC_IRQ_FLAG;
    return (unsigned short)(MG2_MADC_DATA >> 4);
}

static void mg2_dma_copy_words(unsigned channel,
                               unsigned long src,
                               unsigned long dst,
                               unsigned long count)
{
    MG2_DMA_CTRL(channel) = MG2_DMA_RESET;
    MG2_DMA_SRC_LO(channel) = (unsigned short)src;
    MG2_DMA_SRC_HI(channel) = (unsigned short)(src >> 16);
    MG2_DMA_DST_LO(channel) = (unsigned short)dst;
    MG2_DMA_DST_HI(channel) = (unsigned short)(dst >> 16);
    MG2_DMA_COUNT_LO(channel) = (unsigned short)count;
    MG2_DMA_COUNT_HI(channel) = (unsigned short)(count >> 16);
    MG2_DMA_CTRL(channel) = MG2_DMA_ENABLE;
}

#endif /* MOBIGO2_HW_H */
