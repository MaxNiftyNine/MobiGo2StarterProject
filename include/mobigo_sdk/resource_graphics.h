#ifndef MOBIGO_SDK_RESOURCE_GRAPHICS_H
#define MOBIGO_SDK_RESOURCE_GRAPHICS_H

#include "mobigo_sdk/resource_bundle.h"

enum mg_sdk_resource_graphics_layout {
    MG_SDK_UI_B_RECORD_WORDS = 14,
    MG_SDK_COMPONENT_REFERENCE_WORDS = 4,
    MG_SDK_BITMAP_DESCRIPTOR_WORDS = 6,
    MG_SDK_BITMAP_CHUNK_WORDS = 4,

    MG_SDK_COMPONENT_WORD_X_OFFSET = 0,
    MG_SDK_COMPONENT_WORD_Y_OFFSET = 1,
    MG_SDK_COMPONENT_WORD_BITMAP = 2,

    MG_SDK_BITMAP_WORD_FORMAT = 0,
    MG_SDK_BITMAP_WORD_WIDTH = 1,
    MG_SDK_BITMAP_WORD_HEIGHT = 2,
    MG_SDK_BITMAP_WORD_RESERVED = 3,
    MG_SDK_BITMAP_WORD_CHUNK_TABLE = 4,

    MG_SDK_BITMAP_CHUNK_WORD_DIMENSIONS = 0,
    MG_SDK_BITMAP_CHUNK_WORD_FLAGS = 1,
    MG_SDK_BITMAP_CHUNK_WORD_DATA = 2
};

enum mg_sdk_ui_b_record_layout {
    MG_SDK_UI_B_RECORD_WORD_DELTA_X = 0,
    MG_SDK_UI_B_RECORD_WORD_DELTA_Y = 1,
    MG_SDK_UI_B_RECORD_WORD_DURATION = 2,
    MG_SDK_UI_B_RECORD_WORD_MIN_Y = 3,
    MG_SDK_UI_B_RECORD_WORD_MAX_Y = 4,
    MG_SDK_UI_B_RECORD_WORD_MIN_X = 5,
    MG_SDK_UI_B_RECORD_WORD_MAX_X = 6,
    MG_SDK_UI_B_RECORD_WORD_RESERVED_7 = 7,
    /* 0xffffffff disables the transition-notification payload. */
    MG_SDK_UI_B_RECORD_WORD_EVENT_TOKEN = 8,
    MG_SDK_UI_B_RECORD_WORD_COMPONENTS = 10,
    MG_SDK_UI_B_RECORD_WORD_RUNTIME_SLOT = 12
};

/*
 * The bitmap format word is split into a resident-renderer format code in
 * bits 7..0 and sprite-palette selection in bits 12..8:
 *
 *   bits 7..0  resource pixel-format code
 *   bits 11..8 PPU palette selector
 *   bit 12     select the additional 0x200-entry sprite palette bank
 *
 * Codes 0, 1, and 2 map to 2, 4, and 6 bits per pixel. Codes 3 through
 * 8 select resident 8-bpp paths. A complete census of 1,946 unique primary
 * family-B bitmaps across G1/G2/G3/G4/SY/TM uses only codes 0/1/2; the higher
 * paths are present in resident code but are not emitted by this corpus.
 */
enum mg_sdk_bitmap_format_layout {
    MG_SDK_BITMAP_FORMAT_CODE_MASK = 0x00ff,
    MG_SDK_BITMAP_FORMAT_PALETTE_SHIFT = 8,
    MG_SDK_BITMAP_FORMAT_PALETTE_MASK = 0x0f00,
    MG_SDK_BITMAP_FORMAT_EXTENDED_PALETTE = 0x1000,

    MG_SDK_BITMAP_FORMAT_2BPP = 0,
    MG_SDK_BITMAP_FORMAT_4BPP = 1,
    MG_SDK_BITMAP_FORMAT_6BPP = 2,
    MG_SDK_BITMAP_FORMAT_8BPP = 3
};

/*
 * The resident family-B sprite emitter has explicit size-code branches only
 * for 16, 32, and 64 pixels on each chunk axis. The complete retail corpus
 * contains all nine combinations of these three axis sizes and no other
 * family-B chunk dimension. An 8x8 clean-room experiment reproduced the
 * failure mode: stale sprite-size state caused the renderer to sample beyond
 * the authored payload. Validate authored family-B chunks with these helpers.
 */
enum mg_sdk_bitmap_chunk_axis_size {
    MG_SDK_BITMAP_CHUNK_AXIS_16 = 16,
    MG_SDK_BITMAP_CHUNK_AXIS_32 = 32,
    MG_SDK_BITMAP_CHUNK_AXIS_64 = 64
};

enum mg_sdk_rgb555_layout {
    MG_SDK_RGB555_BLUE_MASK = 0x001f,
    MG_SDK_RGB555_GREEN_MASK = 0x03e0,
    MG_SDK_RGB555_RED_MASK = 0x7c00,
    MG_SDK_RGB555_TRANSPARENT = 0x8000,
    MG_SDK_DEFAULT_SPRITE_PALETTE_BANK = 0x0100
};

/*
 * A component list starts with a 32-bit count and is followed by these
 * records. Cross-title geometry strongly identifies words 0/1 as signed X/Y
 * offsets. Words 2..3 are a bundle-relative bitmap-descriptor pointer before
 * registration.
 */
struct mg_sdk_component_reference {
    mg_sdk_u16 word[MG_SDK_COMPONENT_REFERENCE_WORDS];
};

/*
 * A family-B mode starts with a 32-bit record count followed by these
 * 14-word records. The resident transition engine applies the destination
 * record's delta X/Y when it advances, accumulates duration in ticks, and uses min/max offsets
 * for orientation-aware visibility/culling around the object's X/Y anchor.
 * Words 8..9 are copied into transition event 0x0200 when not 0xffffffff.
 * Words 10..11 point to the counted component list and 12..13 to private
 * mutable runtime storage. Word 7 is still deliberately unnamed.
 */
struct mg_sdk_ui_b_record {
    mg_sdk_u16 word[MG_SDK_UI_B_RECORD_WORDS];
};

mg_sdk_s16 mg_sdk_ui_b_record_delta_x(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_delta_y(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_u16 mg_sdk_ui_b_record_duration(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_min_x(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_max_x(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_min_y(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_max_y(
    const struct mg_sdk_ui_b_record *record);

/*
 * Author one complete family-B animation/timeline record. Pointer arguments
 * are linked bundle-relative word pointers before registration. A component
 * pointer may reference any counted component list, allowing multi-part
 * sprites; runtime_slot_pointer normally references a private zeroed pair.
 */
void mg_sdk_ui_b_record_build(
    struct mg_sdk_ui_b_record *record,
    mg_sdk_s16 delta_x,
    mg_sdk_s16 delta_y,
    mg_sdk_u16 duration,
    mg_sdk_s16 min_y,
    mg_sdk_s16 max_y,
    mg_sdk_s16 min_x,
    mg_sdk_s16 max_x,
    mg_sdk_u32 event_token,
    mg_sdk_u32 component_pointer,
    mg_sdk_u32 runtime_slot_pointer);

struct mg_sdk_bitmap_descriptor {
    mg_sdk_u16 word[MG_SDK_BITMAP_DESCRIPTOR_WORDS];
};

/*
 * Chunk dimensions are byte-packed: width in bits 7..0 and height in
 * bits 15..8. Words 2..3 are normally a primary-storage-relative data pointer.
 * In the 4,232 catalogued primary family-B chunks, word 1 is always zero and
 * every data pointer is in the 0x80000000 primary class. Keep word 1 as a
 * reserved/flags field because the renderer still accepts it.
 */
struct mg_sdk_bitmap_chunk {
    mg_sdk_u16 word[MG_SDK_BITMAP_CHUNK_WORDS];
};

mg_sdk_s16 mg_sdk_component_x_offset(
    const struct mg_sdk_component_reference *component);
mg_sdk_s16 mg_sdk_component_y_offset(
    const struct mg_sdk_component_reference *component);
void mg_sdk_component_build(
    struct mg_sdk_component_reference *component,
    mg_sdk_s16 x_offset,
    mg_sdk_s16 y_offset,
    mg_sdk_u32 bitmap_pointer);

mg_sdk_u16 mg_sdk_bitmap_width(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_height(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_format_code(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_bits_per_pixel(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_palette_selector(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_uses_extended_palette(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_pack_format(
    mg_sdk_u16 format_code,
    mg_sdk_u16 palette_selector,
    mg_sdk_u16 use_extended_palette);
mg_sdk_u16 mg_sdk_bitmap_default_sprite_palette_index(
    const struct mg_sdk_bitmap_descriptor *bitmap);
void mg_sdk_bitmap_build(
    struct mg_sdk_bitmap_descriptor *bitmap,
    mg_sdk_u16 format_word,
    mg_sdk_u16 width,
    mg_sdk_u16 height,
    mg_sdk_u32 chunk_table_pointer);
mg_sdk_u16 mg_sdk_rgb555_pack(
    mg_sdk_u16 red,
    mg_sdk_u16 green,
    mg_sdk_u16 blue,
    mg_sdk_u16 transparent);

mg_sdk_u16 mg_sdk_bitmap_chunk_width(
    const struct mg_sdk_bitmap_chunk *chunk);
mg_sdk_u16 mg_sdk_bitmap_chunk_height(
    const struct mg_sdk_bitmap_chunk *chunk);
mg_sdk_u16 mg_sdk_bitmap_chunk_axis_supported(mg_sdk_u16 dimension);
mg_sdk_u16 mg_sdk_bitmap_chunk_dimensions_supported(
    mg_sdk_u16 width,
    mg_sdk_u16 height);
mg_sdk_u16 mg_sdk_bitmap_pack_chunk_dimensions(
    mg_sdk_u16 width,
    mg_sdk_u16 height);
int mg_sdk_bitmap_chunk_build(
    struct mg_sdk_bitmap_chunk *chunk,
    mg_sdk_u16 width,
    mg_sdk_u16 height,
    mg_sdk_u16 flags,
    mg_sdk_u32 primary_data_pointer);

/*
 * Confirmed standard-settings pixel packing: eight 2-bit palette indices
 * occupy one little-endian u'nSP word. Pixels 0..3 occupy low-byte bits
 * 7..0, most-significant pair first; pixels 4..7 use the high byte likewise.
 */
mg_sdk_u16 mg_sdk_bitmap_pack_2bpp_word(const mg_sdk_u16 *pixels);
mg_sdk_u16 mg_sdk_bitmap_unpack_2bpp_pixel(
    mg_sdk_u16 packed,
    mg_sdk_u16 index);

#endif
