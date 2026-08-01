#ifndef MOBIGO_SDK_RESOURCE_BUNDLE_H
#define MOBIGO_SDK_RESOURCE_BUNDLE_H

#include "mobigo_sdk/system_controls.h"

/*
 * Partially recovered linked-asset bundle format.
 *
 * All offsets and sizes below are u'nSP 16-bit words. Before resident service
 * 0x075f00 registers a bundle, its table pointers are relative to the first
 * word after this 0x20-word header. Registration rebases those pointers in
 * place, so a registered header is not byte-for-byte identical to its MBA
 * representation.
 */
enum mg_sdk_asset_bundle_layout {
    MG_SDK_ASSET_BUNDLE_HEADER_WORDS = 0x20,
    MG_SDK_ASSET_BUNDLE_UI_A_DESCRIPTOR_WORDS = 10,
    MG_SDK_ASSET_BUNDLE_UI_A_IMAGE_WORDS = 18,
    MG_SDK_ASSET_BUNDLE_UI_B_DESCRIPTOR_WORDS = 12,
    MG_SDK_ASSET_BUNDLE_FIVE_MODE_SETTING_COUNT = 5,
    MG_SDK_ASSET_BUNDLE_SETTING_RECORD_WORDS = 14,

    MG_SDK_ASSET_BUNDLE_WORD_STATE = 0x00,
    MG_SDK_ASSET_BUNDLE_WORD_PALETTE_EVEN_BANKS = 0x02,
    MG_SDK_ASSET_BUNDLE_WORD_PALETTE_ODD_BANKS = 0x04,
    MG_SDK_ASSET_BUNDLE_WORD_PALETTE_000 = 0x02,
    MG_SDK_ASSET_BUNDLE_WORD_PALETTE_100 = 0x04,
    /* Older working names retained as source-compatible aliases. */
    MG_SDK_ASSET_BUNDLE_WORD_PRIMARY_WINDOW_0 = 0x02,
    MG_SDK_ASSET_BUNDLE_WORD_PRIMARY_WINDOW_1 = 0x04,
    MG_SDK_ASSET_BUNDLE_WORD_SECONDARY_WINDOW_0 = 0x06,
    MG_SDK_ASSET_BUNDLE_WORD_SECONDARY_WINDOW_1 = 0x08,
    MG_SDK_ASSET_BUNDLE_WORD_LOOKUP_COUNT = 0x0a,
    MG_SDK_ASSET_BUNDLE_WORD_LOOKUP_TABLE = 0x0c,
    MG_SDK_ASSET_BUNDLE_WORD_AUX_TABLE = 0x10,
    MG_SDK_ASSET_BUNDLE_WORD_UI_A_COUNT = 0x12,
    MG_SDK_ASSET_BUNDLE_WORD_UI_A_TABLE = 0x14,
    MG_SDK_ASSET_BUNDLE_WORD_UI_B_COUNT = 0x16,
    MG_SDK_ASSET_BUNDLE_WORD_UI_B_TABLE = 0x18,
    MG_SDK_ASSET_BUNDLE_WORD_AUTO_INSTANCE_TABLE = 0x1a,
    /* Older working name retained as a source-compatible alias. */
    MG_SDK_ASSET_BUNDLE_WORD_GENERATED_HANDLES =
        MG_SDK_ASSET_BUNDLE_WORD_AUTO_INSTANCE_TABLE
};

enum mg_sdk_asset_bundle_auto_instance_layout {
    MG_SDK_ASSET_BUNDLE_AUTO_INSTANCE_WORDS_PER_ENTRY = 2
};

/*
 * Header words 0x1a..0x1b point at two parallel arrays, both indexed by the
 * flattened descriptor order [all family-A descriptors, then all family-B
 * descriptors]:
 *
 *   marker array: 2 * (A_count + B_count) words
 *   handle array: 2 * (A_count + B_count) words
 *
 * A zero marker skips the descriptor. A nonzero marker asks registration to
 * instantiate that descriptor; service 0x075f00 then writes the returned
 * 32-bit resident handle into the matching entry of the second array. TM uses
 * marker value 1 for family-A descriptor zero, and emulator validation of a
 * clean-room bundle produces handle 0x90000000 in its output slot.
 */

enum mg_sdk_ui_family_a_layout {
    /* The linked 10-word descriptor stores its nested image pointer here. */
    MG_SDK_UI_A_DESCRIPTOR_WORD_IMAGE = 0x08,

    /* Renderer-confirmed fields in the 18-word nested image record. */
    MG_SDK_UI_A_IMAGE_WORD_WIDTH = 0x00,
    MG_SDK_UI_A_IMAGE_WORD_HEIGHT = 0x01,
    MG_SDK_UI_A_IMAGE_WORD_CELL_WIDTH = 0x02,
    MG_SDK_UI_A_IMAGE_WORD_CELL_HEIGHT = 0x03,
    MG_SDK_UI_A_IMAGE_WORD_FORMAT = 0x04,
    MG_SDK_UI_A_IMAGE_WORD_GRAPHICS_BASE = 0x0a,
    MG_SDK_UI_A_IMAGE_WORD_TILEMAP_SOURCE = 0x0c,
    MG_SDK_UI_A_IMAGE_WORD_PALETTE_SELECTOR = 0x0e,
    MG_SDK_UI_A_IMAGE_WORD_RUNTIME_SLOT = 0x10
};

enum mg_sdk_ui_family_b_descriptor_layout {
    MG_SDK_UI_B_DESCRIPTOR_WORD_VISIBLE = 0x00,
    MG_SDK_UI_B_DESCRIPTOR_WORD_X = 0x01,
    MG_SDK_UI_B_DESCRIPTOR_WORD_Y = 0x02,
    MG_SDK_UI_B_DESCRIPTOR_WORD_STATE_3 = 0x03,
    MG_SDK_UI_B_DESCRIPTOR_WORD_ORIENTATION = 0x04,
    MG_SDK_UI_B_DESCRIPTOR_WORD_MODE = 0x05,
    /* Descriptor word 6 is copied to runtime-object word 8. */
    MG_SDK_UI_B_DESCRIPTOR_WORD_OBJECT_STATE_8 = 0x06,
    /* Renderer-confirmed 0..0x40 object intensity/opacity default. */
    MG_SDK_UI_B_DESCRIPTOR_WORD_OPACITY = 0x07,
    MG_SDK_UI_B_DESCRIPTOR_WORD_8 = 0x08,
    MG_SDK_UI_B_DESCRIPTOR_WORD_9 = 0x09,
    MG_SDK_UI_B_DESCRIPTOR_WORD_GRAPH = 0x0a
};

#define MG_SDK_BUNDLE_PRIMARY_RELATIVE_TAG ((mg_sdk_u32)0x80000000UL)
#define MG_SDK_BUNDLE_SECONDARY_RELATIVE_TAG ((mg_sdk_u32)0xc0000000UL)
#define MG_SDK_BUNDLE_PRIMARY_OFFSET_MASK ((mg_sdk_u32)0x7fffffffUL)
#define MG_SDK_BUNDLE_SECONDARY_OFFSET_MASK ((mg_sdk_u32)0x3fffffffUL)

/*
 * G1, G2, and SY use this full five-mode ordering. G3/G4 link compacted
 * variants, so runtime code must use indices generated with its own bundle.
 */
enum mg_sdk_five_mode_setting {
    MG_SDK_FIVE_MODE_BRIGHTNESS = 1,
    MG_SDK_FIVE_MODE_VOLUME = 4
};

/*
 * Raw layouts are deliberate: several fields remain unknown. Keeping them as
 * words prevents host ABI padding from changing the target image encoding.
 */
struct mg_sdk_asset_bundle_header {
    mg_sdk_u16 word[MG_SDK_ASSET_BUNDLE_HEADER_WORDS];
};

/*
 * During version-2 registration, the two tagged pointers at words 2 and 4
 * supply 0x200 RGB555 entries each. The first source's halves populate
 * hardware palette banks 0x000 and 0x200; the second source populates 0x100
 * and 0x300. Sprite palette control starts with its +0x100 bank enabled in
 * the inspected runtime.
 */

struct mg_sdk_ui_family_a_descriptor {
    mg_sdk_u16 word[MG_SDK_ASSET_BUNDLE_UI_A_DESCRIPTOR_WORDS];
};

/*
 * Family-A descriptor words 8..9 point at this 18-word linked image record.
 * The resident renderer proves words 0/1 are source dimensions and words 2/3
 * are cell dimensions: it divides width by cell width and height by cell
 * height before allocating/emitting the temporary tilemap. Word 4 is passed
 * to the background pixel-format selector. Words 10..11 are passed directly
 * to the PPU background graphics-base setter, words 12..13 are used as the
 * source of tilemap/index data, and word 14 is the PPU background palette
 * selector. Words 16..17 point to a private two-word zero-initialized mutable
 * slot. Words 5..9 and word 15 deliberately remain unnamed.
 */
struct mg_sdk_ui_family_a_image_record {
    mg_sdk_u16 word[MG_SDK_ASSET_BUNDLE_UI_A_IMAGE_WORDS];
};

struct mg_sdk_ui_family_b_descriptor {
    mg_sdk_u16 word[MG_SDK_ASSET_BUNDLE_UI_B_DESCRIPTOR_WORDS];
};

/*
 * A settings-mode table starts with a 32-bit record count followed by these
 * 14-word records. Words 10..11 are a relative pointer to a component list.
 * Words 12..13 are a relative pointer to a private two-word zero-initialized
 * runtime slot. The remaining fields are intentionally unnamed until their
 * renderer semantics are independently verified.
 */
struct mg_sdk_setting_record {
    mg_sdk_u16 word[MG_SDK_ASSET_BUNDLE_SETTING_RECORD_WORDS];
};

mg_sdk_u32 mg_sdk_bundle_read_word_pair(
    const mg_sdk_u16 *words,
    mg_sdk_u16 word_offset);

void mg_sdk_bundle_write_word_pair(
    mg_sdk_u16 *words,
    mg_sdk_u16 word_offset,
    mg_sdk_u32 value);

mg_sdk_u32 mg_sdk_bundle_relative_to_word_address(
    mg_sdk_u32 header_word_address,
    mg_sdk_u32 relative_word_pointer);

mg_sdk_u32 mg_sdk_bundle_primary_relative(mg_sdk_u32 word_offset);
mg_sdk_u32 mg_sdk_bundle_secondary_relative(mg_sdk_u32 word_offset);

mg_sdk_u16 mg_sdk_bundle_auto_instance_table_words(
    mg_sdk_u16 descriptor_count);

void mg_sdk_bundle_auto_instance_set_marker(
    mg_sdk_u16 *table,
    mg_sdk_u16 descriptor_index,
    mg_sdk_u32 marker);

mg_sdk_u32 mg_sdk_bundle_auto_instance_read_handle(
    const mg_sdk_u16 *table,
    mg_sdk_u16 descriptor_count,
    mg_sdk_u16 descriptor_index);

#endif
