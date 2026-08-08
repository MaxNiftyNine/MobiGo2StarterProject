#ifndef MOBIGO_SDK_MEMORY_MAP_H
#define MOBIGO_SDK_MEMORY_MAP_H

/*
 * Conservative title-owned word-address ranges used by the maintained SDK
 * applications.  Addresses are u'nSP 16-bit word addresses, not byte offsets.
 *
 * The resident launcher and its stack remain live while an MBA runs.  Do not
 * place application arenas below TITLE_RAM_BEGIN or at/above TITLE_RAM_END,
 * and do not assume that the linker initializes writable globals for a direct
 * MBA entry.  Immutable data belongs in const storage; mutable arenas must be
 * initialized explicitly before use.
 */
#define MG_SDK_TITLE_RAM_BEGIN ((unsigned long)0x5000UL)
#define MG_SDK_TITLE_RAM_END   ((unsigned long)0x6800UL)

/* Default starter allocations.  The UI reservation is intentionally larger
 * than the current generated graph so future clean-room artwork can grow
 * without colliding with the standard-controls state. */
#define MG_SDK_DEFAULT_SYSTEM_UI_WORD_ADDRESS \
    ((unsigned long)0x5000UL)
#define MG_SDK_DEFAULT_SYSTEM_UI_RESERVED_WORDS \
    ((unsigned long)0x0800UL)
#define MG_SDK_DEFAULT_STANDARD_CONTROLS_WORD_ADDRESS \
    ((unsigned long)0x5800UL)
#define MG_SDK_DEFAULT_STANDARD_CONTROLS_RESERVED_WORDS \
    ((unsigned long)0x0040UL)

/* One SDK-owned word is used as the fixed source for DMA fills.  Application
 * arenas must end before it.  Keeping the seed outside linker-owned storage
 * also makes fills work when their destination is above the CPU's directly
 * addressable window. */
#define MG_SDK_HARDWARE_SCRATCH_WORD_ADDRESS \
    ((unsigned long)0x67ffUL)

#define MG_SDK_WORD_RANGE_END(first, words) \
    ((unsigned long)(first) + (unsigned long)(words))
#define MG_SDK_WORD_RANGES_OVERLAP(first_a, words_a, first_b, words_b) \
    (MG_SDK_WORD_RANGE_END((first_a), (words_a)) > (unsigned long)(first_b) && \
     MG_SDK_WORD_RANGE_END((first_b), (words_b)) > (unsigned long)(first_a))

#if (0x5000UL + 0x0800UL) > 0x5800UL
#error default system-UI and standard-controls arenas overlap
#endif
#if 0x5800UL >= 0x6800UL
#error default standard-controls state lies outside title RAM
#endif
#if (0x5800UL + 0x0040UL) > 0x67ffUL
#error default standard-controls arena overlaps the hardware scratch word
#endif

#endif
