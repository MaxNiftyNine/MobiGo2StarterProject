/* MobiGo 2 Bad Apple proof-of-concept player.
 *
 * Movie data is generated into a linked const resource by build.py. Frames are
 * 1-bpp, XOR-delta encoded, then word-run encoded.  A token with bit 15 clear
 * skips unchanged bitmap words; a token with bit 15 set is followed by that
 * many XOR words.  Each frame starts with its encoded size in words.
 *
 * A short unsigned 8-bit PCM resource is linked beside the movie. Channel 0
 * of the GPL16250 SPU loops it in hardware, independently of video playback.
 */

#include "generated_media.h"

#define REG16(a) (*(volatile unsigned short *)(a))
#define WORD_PTR(a) ((volatile unsigned short *)(a))

#define MOVIE_W 64u
#define MOVIE_H 48u
#define MOVIE_WORDS_PER_ROW 4u
#define MOVIE_SCALE 5u
#define BITMAP_WORDS 192u
#define EXPANDED_ROW_WORDS 320u
#define BITMAP_ADDR 0x6000UL
#define EXPANDED_ROW_ADDR 0x6100UL

#define MOVIE_ADDR ((unsigned long)sample_movie_words)
#define MOVIE_FRAMES SAMPLE_MOVIE_FRAME_COUNT
#define AUDIO_ADDR ((unsigned long)sample_audio_words)

#define AUDIO_RATE 4000UL
#define SPU_CLOCK 281250UL
#define AUDIO_PHASE ((AUDIO_RATE * 524288UL + (SPU_CLOCK / 2UL)) / SPU_CLOCK)

#define BITMAP WORD_PTR(BITMAP_ADDR)
#define EXPANDED_ROW WORD_PTR(EXPANDED_ROW_ADDR)

static void service_watchdog(void)
{
    REG16(0x780b) = 0xa005;
}

/* This is the channel-0 PCM setup from Generalplus's official GPF32001A
 * SPU_PCM example, adapted for an MBA-resident unsigned 8-bit sample.
 * AUTO_REPEAT follows the 0xffff terminator back to the loop address. */
static void start_audio(void)
{
    unsigned short high;
    unsigned short mode;

    high = (unsigned short)((AUDIO_ADDR >> 16) & 0x003fUL);
    mode = (unsigned short)(0x2000u | high | (high << 6));

    /* Stop only channel 0 while retaining any loader-owned channels. */
    REG16(0x7b80) &= 0xfffeu;
    REG16(0x7b82) &= 0xfffeu; /* channel FIQ disabled */
    REG16(0x7b8c) &= 0xfffeu; /* zero-cross stop disabled */

    REG16(0x7b8d) = 0x88c8u; /* saturate, compressor, 1:1 volume, init */
    REG16(0x7b81) = 0x007fu; /* full main volume */
    REG16(0x7b8e) = 0xf007u; /* peak compressor, infinite ratio */
    REG16(0x7b9a) = 0x8080u;

    REG16(0x7c00) = (unsigned short)(AUDIO_ADDR & 0xffffUL);
    REG16(0x7c01) = mode; /* 8-bit PCM, hardware auto-repeat */
    REG16(0x7c02) = (unsigned short)(AUDIO_ADDR & 0xffffUL);
    REG16(0x7c03) = 0x4040u; /* centered, equal left/right volume */
    REG16(0x7c05) = 0x007fu; /* full manual envelope */
    REG16(0x7c09) = 0x8000u;
    REG16(0x7c0b) = 0x8000u;
    REG16(0x7c0d) = 0x0008u; /* initialize SPU sample state */

    REG16(0x7e00) = (unsigned short)((AUDIO_PHASE >> 16) & 0x0007UL);
    REG16(0x7e04) = (unsigned short)(AUDIO_PHASE & 0xffffUL);
    REG16(0x7e01) = 0;
    REG16(0x7e05) = 0;

    REG16(0x7b95) |= 0x0001u; /* channel 0 manual envelope */
    REG16(0x7b94) |= 0x0001u; /* channel 0 repeat */
    REG16(0x7b8b) = 0x0001u;  /* acknowledge old stop latch */

    /* Match the MobiGo retail sound-driver startup, not merely the generic
     * GPF32001A SDK board. LD closes the board-specific 0x78ff output gate
     * immediately before entering an MBA, so the application must reopen it.
     * Both DAC halves are enabled because the MobiGo speaker path uses the
     * retail stereo configuration. */
    REG16(0x78f0) = 0;
    REG16(0x78f8) = 0;
    REG16(0x78f0) = 0x8000u;
    REG16(0x78f8) = 0x8000u;
    REG16(0x78f0) = 0;
    REG16(0x78f8) = 0;
    REG16(0x78f0) = 0x3800u;
    REG16(0x78f8) = 0x3000u;
    REG16(0x78ff) = 0x0001u;
    REG16(0x7b80) |= 0x0001u;
}

static void assert_scanout(unsigned short fbi_low, unsigned short fbi_high)
{
    REG16(0x7078) = fbi_low & 0xfff0;
    REG16(0x7079) = fbi_high & 0x07ff;
    REG16(0x707a) = fbi_low & 0xfff0;
    REG16(0x707b) = fbi_high & 0x07ff;
    REG16(0x707f) = 0x0088;
}

/* Copy an MBA-resident block into a physical SDRAM framebuffer. This is the
 * GPL16250VA system-DMA software-mode sequence. */
static void copy_block_to_physical(unsigned long source,
                                   unsigned long destination,
                                   unsigned short words)
{
    unsigned long timeout;

    REG16(0x7a80) = 0x0200;
    REG16(0x7abf) = 0x0001;
    REG16(0x7a81) = (unsigned short)(source & 0xffffUL);
    REG16(0x7a84) = (unsigned short)((source >> 16) & 0x07ffUL);
    REG16(0x7a82) = (unsigned short)(destination & 0xfff0UL);
    REG16(0x7a85) = (unsigned short)((destination >> 16) & 0x07ffUL);
    REG16(0x7a83) = words;
    REG16(0x7a86) = 0;
    REG16(0x7a80) = 0x0009; /* normal completion mode + DMA enable */

    timeout = 0x000fffffUL;
    while (!(REG16(0x7abf) & 0x0001) && timeout != 0) {
        --timeout;
        service_watchdog();
    }
    REG16(0x7abf) = 0x0001;
}

static void clear_bitmap(void)
{
    unsigned i;
    for (i = 0; i < BITMAP_WORDS; ++i) {
        BITMAP[i] = 0;
        if ((i & 31u) == 0u) service_watchdog();
    }
}

static volatile unsigned short *decode_frame(volatile unsigned short *src)
{
    volatile unsigned short *end = src + *src + 1;
    unsigned pos = 0;
    ++src;
    while (src < end) {
        unsigned short token = *src++;
        unsigned count = token & 0x7fff;
        if (token & 0x8000) {
            while (count--) BITMAP[pos++] ^= *src++;
        } else {
            pos += count;
        }
        service_watchdog();
    }
    return end;
}

static void expand_and_present(unsigned short fbi_low,
                               unsigned short fbi_high,
                               unsigned short fbo_low,
                               unsigned short fbo_high)
{
    unsigned long fbi;
    unsigned long fbo;
    unsigned long source;
    unsigned y;

    fbi = ((unsigned long)(fbi_high & 0x07ff) << 16) |
          (unsigned long)(fbi_low & 0xfff0);
    fbo = ((unsigned long)(fbo_high & 0x07ff) << 16) |
          (unsigned long)(fbo_low & 0xfff0);
    source = EXPANDED_ROW_ADDR;

    for (y = 0; y < MOVIE_H; ++y) {
        unsigned repeat_y;
        unsigned out = 0;
        unsigned word_index;
        for (word_index = 0; word_index < MOVIE_WORDS_PER_ROW; ++word_index) {
            unsigned short bits = BITMAP[y * MOVIE_WORDS_PER_ROW + word_index];
            unsigned mask;
            for (mask = 0x8000; mask; mask >>= 1) {
                unsigned short color = (bits & mask) ? 0xffff : 0x0000;
                unsigned repeat_x;
                for (repeat_x = 0; repeat_x < MOVIE_SCALE; ++repeat_x) {
                    EXPANDED_ROW[out++] = color;
                }
            }
        }
        service_watchdog();
        for (repeat_y = 0; repeat_y < MOVIE_SCALE; ++repeat_y) {
            unsigned long line =
                (unsigned long)(y * MOVIE_SCALE + repeat_y) *
                EXPANDED_ROW_WORDS;
            copy_block_to_physical(
                source, fbi + line, EXPANDED_ROW_WORDS);
            if (fbo != fbi) {
                copy_block_to_physical(
                    source, fbo + line, EXPANDED_ROW_WORDS);
            }
        }
    }
}

static void wait_frame(unsigned short fbi_low, unsigned short fbi_high)
{
    volatile unsigned long ticks;
    for (ticks = 0; ticks < 100000UL; ++ticks) {
        if ((ticks & 0x0fffUL) == 0) {
            service_watchdog();
            assert_scanout(fbi_low, fbi_high);
        }
    }
}

int main(void)
{
    unsigned short fbi_low;
    unsigned short fbi_high;
    unsigned short fbo_low;
    unsigned short fbo_high;

    /* This is an LD application callback. Preserve inherited IRQ/FIQ, stay
     * resident, and keep servicing the watchdog for the entire playback. */
    service_watchdog();
    fbi_low = REG16(0x7078);
    fbi_high = REG16(0x7079);
    fbo_low = REG16(0x707a);
    fbo_high = REG16(0x707b);
    start_audio();

    /* The movie is const data in the loaded MBA image. Keep the loader's
     * memory-controller mapping intact. */
    for (;;) {
        volatile unsigned short *movie = WORD_PTR(MOVIE_ADDR);
        unsigned frame;
        clear_bitmap();
        for (frame = 0; frame < MOVIE_FRAMES; ++frame) {
            movie = decode_frame(movie);
            expand_and_present(fbi_low, fbi_high, fbo_low, fbo_high);
            assert_scanout(fbi_low, fbi_high);
            wait_frame(fbi_low, fbi_high);
        }
    }
}
