#include "mobigo_sdk/resource_graphics.h"

static void graphics_put_u32(mg_sdk_u16 *word, mg_sdk_u32 value)
{
    word[0] = (mg_sdk_u16)value;
    word[1] = (mg_sdk_u16)(value >> 16);
}

mg_sdk_s16 mg_sdk_ui_b_record_delta_x(
    const struct mg_sdk_ui_b_record *record)
{
    return (mg_sdk_s16)record->word[MG_SDK_UI_B_RECORD_WORD_DELTA_X];
}

mg_sdk_s16 mg_sdk_ui_b_record_delta_y(
    const struct mg_sdk_ui_b_record *record)
{
    return (mg_sdk_s16)record->word[MG_SDK_UI_B_RECORD_WORD_DELTA_Y];
}

mg_sdk_u16 mg_sdk_ui_b_record_duration(
    const struct mg_sdk_ui_b_record *record)
{
    return record->word[MG_SDK_UI_B_RECORD_WORD_DURATION];
}

mg_sdk_s16 mg_sdk_ui_b_record_min_x(
    const struct mg_sdk_ui_b_record *record)
{
    return (mg_sdk_s16)record->word[MG_SDK_UI_B_RECORD_WORD_MIN_X];
}

mg_sdk_s16 mg_sdk_ui_b_record_max_x(
    const struct mg_sdk_ui_b_record *record)
{
    return (mg_sdk_s16)record->word[MG_SDK_UI_B_RECORD_WORD_MAX_X];
}

mg_sdk_s16 mg_sdk_ui_b_record_min_y(
    const struct mg_sdk_ui_b_record *record)
{
    return (mg_sdk_s16)record->word[MG_SDK_UI_B_RECORD_WORD_MIN_Y];
}

mg_sdk_s16 mg_sdk_ui_b_record_max_y(
    const struct mg_sdk_ui_b_record *record)
{
    return (mg_sdk_s16)record->word[MG_SDK_UI_B_RECORD_WORD_MAX_Y];
}

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
    mg_sdk_u32 runtime_slot_pointer)
{
    if (record == 0) {
        return;
    }
    record->word[MG_SDK_UI_B_RECORD_WORD_DELTA_X] = (mg_sdk_u16)delta_x;
    record->word[MG_SDK_UI_B_RECORD_WORD_DELTA_Y] = (mg_sdk_u16)delta_y;
    record->word[MG_SDK_UI_B_RECORD_WORD_DURATION] = duration;
    record->word[MG_SDK_UI_B_RECORD_WORD_MIN_Y] = (mg_sdk_u16)min_y;
    record->word[MG_SDK_UI_B_RECORD_WORD_MAX_Y] = (mg_sdk_u16)max_y;
    record->word[MG_SDK_UI_B_RECORD_WORD_MIN_X] = (mg_sdk_u16)min_x;
    record->word[MG_SDK_UI_B_RECORD_WORD_MAX_X] = (mg_sdk_u16)max_x;
    record->word[MG_SDK_UI_B_RECORD_WORD_RESERVED_7] = 0;
    graphics_put_u32(
        record->word + MG_SDK_UI_B_RECORD_WORD_EVENT_TOKEN, event_token);
    graphics_put_u32(
        record->word + MG_SDK_UI_B_RECORD_WORD_COMPONENTS, component_pointer);
    graphics_put_u32(
        record->word + MG_SDK_UI_B_RECORD_WORD_RUNTIME_SLOT,
        runtime_slot_pointer);
}

mg_sdk_s16 mg_sdk_component_x_offset(
    const struct mg_sdk_component_reference *component)
{
    return (mg_sdk_s16)
        component->word[MG_SDK_COMPONENT_WORD_X_OFFSET];
}

mg_sdk_s16 mg_sdk_component_y_offset(
    const struct mg_sdk_component_reference *component)
{
    return (mg_sdk_s16)
        component->word[MG_SDK_COMPONENT_WORD_Y_OFFSET];
}

void mg_sdk_component_build(
    struct mg_sdk_component_reference *component,
    mg_sdk_s16 x_offset,
    mg_sdk_s16 y_offset,
    mg_sdk_u32 bitmap_pointer)
{
    if (component == 0) {
        return;
    }
    component->word[MG_SDK_COMPONENT_WORD_X_OFFSET] = (mg_sdk_u16)x_offset;
    component->word[MG_SDK_COMPONENT_WORD_Y_OFFSET] = (mg_sdk_u16)y_offset;
    graphics_put_u32(
        component->word + MG_SDK_COMPONENT_WORD_BITMAP, bitmap_pointer);
}

mg_sdk_u16 mg_sdk_bitmap_width(
    const struct mg_sdk_bitmap_descriptor *bitmap)
{
    return bitmap->word[MG_SDK_BITMAP_WORD_WIDTH];
}

mg_sdk_u16 mg_sdk_bitmap_height(
    const struct mg_sdk_bitmap_descriptor *bitmap)
{
    return bitmap->word[MG_SDK_BITMAP_WORD_HEIGHT];
}

mg_sdk_u16 mg_sdk_bitmap_format_code(
    const struct mg_sdk_bitmap_descriptor *bitmap)
{
    return bitmap->word[MG_SDK_BITMAP_WORD_FORMAT] &
        MG_SDK_BITMAP_FORMAT_CODE_MASK;
}

mg_sdk_u16 mg_sdk_bitmap_bits_per_pixel(
    const struct mg_sdk_bitmap_descriptor *bitmap)
{
    mg_sdk_u16 code = mg_sdk_bitmap_format_code(bitmap);
    if (code <= MG_SDK_BITMAP_FORMAT_6BPP) {
        return (code + 1) * 2;
    }
    if (code <= 8) {
        return 8;
    }
    return 0;
}

mg_sdk_u16 mg_sdk_bitmap_palette_selector(
    const struct mg_sdk_bitmap_descriptor *bitmap)
{
    return (
        bitmap->word[MG_SDK_BITMAP_WORD_FORMAT] &
        MG_SDK_BITMAP_FORMAT_PALETTE_MASK
    ) >> MG_SDK_BITMAP_FORMAT_PALETTE_SHIFT;
}

mg_sdk_u16 mg_sdk_bitmap_uses_extended_palette(
    const struct mg_sdk_bitmap_descriptor *bitmap)
{
    return (
        bitmap->word[MG_SDK_BITMAP_WORD_FORMAT] &
        MG_SDK_BITMAP_FORMAT_EXTENDED_PALETTE
    ) != 0;
}

mg_sdk_u16 mg_sdk_bitmap_pack_format(
    mg_sdk_u16 format_code,
    mg_sdk_u16 palette_selector,
    mg_sdk_u16 use_extended_palette)
{
    mg_sdk_u16 result =
        (format_code & MG_SDK_BITMAP_FORMAT_CODE_MASK) |
        (
            (palette_selector & 0x000f) <<
            MG_SDK_BITMAP_FORMAT_PALETTE_SHIFT
        );
    if (use_extended_palette != 0) {
        result |= MG_SDK_BITMAP_FORMAT_EXTENDED_PALETTE;
    }
    return result;
}

mg_sdk_u16 mg_sdk_bitmap_default_sprite_palette_index(
    const struct mg_sdk_bitmap_descriptor *bitmap)
{
    mg_sdk_u16 result =
        MG_SDK_DEFAULT_SPRITE_PALETTE_BANK +
        mg_sdk_bitmap_palette_selector(bitmap) * 0x10;
    if (mg_sdk_bitmap_uses_extended_palette(bitmap) != 0) {
        result += 0x200;
    }
    return result;
}

void mg_sdk_bitmap_build(
    struct mg_sdk_bitmap_descriptor *bitmap,
    mg_sdk_u16 format_word,
    mg_sdk_u16 width,
    mg_sdk_u16 height,
    mg_sdk_u32 chunk_table_pointer)
{
    if (bitmap == 0) {
        return;
    }
    bitmap->word[MG_SDK_BITMAP_WORD_FORMAT] = format_word;
    bitmap->word[MG_SDK_BITMAP_WORD_WIDTH] = width;
    bitmap->word[MG_SDK_BITMAP_WORD_HEIGHT] = height;
    bitmap->word[MG_SDK_BITMAP_WORD_RESERVED] = 0;
    graphics_put_u32(
        bitmap->word + MG_SDK_BITMAP_WORD_CHUNK_TABLE, chunk_table_pointer);
}

mg_sdk_u16 mg_sdk_rgb555_pack(
    mg_sdk_u16 red,
    mg_sdk_u16 green,
    mg_sdk_u16 blue,
    mg_sdk_u16 transparent)
{
    mg_sdk_u16 result =
        ((red & 0x1f) << 10) |
        ((green & 0x1f) << 5) |
        (blue & 0x1f);
    if (transparent != 0) {
        result |= MG_SDK_RGB555_TRANSPARENT;
    }
    return result;
}

mg_sdk_u16 mg_sdk_bitmap_chunk_width(
    const struct mg_sdk_bitmap_chunk *chunk)
{
    return chunk->word[MG_SDK_BITMAP_CHUNK_WORD_DIMENSIONS] & 0x00ff;
}

mg_sdk_u16 mg_sdk_bitmap_chunk_height(
    const struct mg_sdk_bitmap_chunk *chunk)
{
    return chunk->word[MG_SDK_BITMAP_CHUNK_WORD_DIMENSIONS] >> 8;
}

mg_sdk_u16 mg_sdk_bitmap_chunk_axis_supported(mg_sdk_u16 dimension)
{
    return dimension == MG_SDK_BITMAP_CHUNK_AXIS_16 ||
        dimension == MG_SDK_BITMAP_CHUNK_AXIS_32 ||
        dimension == MG_SDK_BITMAP_CHUNK_AXIS_64;
}

mg_sdk_u16 mg_sdk_bitmap_chunk_dimensions_supported(
    mg_sdk_u16 width,
    mg_sdk_u16 height)
{
    return mg_sdk_bitmap_chunk_axis_supported(width) &&
        mg_sdk_bitmap_chunk_axis_supported(height);
}

mg_sdk_u16 mg_sdk_bitmap_pack_chunk_dimensions(
    mg_sdk_u16 width,
    mg_sdk_u16 height)
{
    return (width & 0x00ff) | ((height & 0x00ff) << 8);
}

int mg_sdk_bitmap_chunk_build(
    struct mg_sdk_bitmap_chunk *chunk,
    mg_sdk_u16 width,
    mg_sdk_u16 height,
    mg_sdk_u16 flags,
    mg_sdk_u32 primary_data_pointer)
{
    if (chunk == 0 ||
        !mg_sdk_bitmap_chunk_dimensions_supported(width, height)) {
        return 0;
    }
    chunk->word[MG_SDK_BITMAP_CHUNK_WORD_DIMENSIONS] =
        mg_sdk_bitmap_pack_chunk_dimensions(width, height);
    chunk->word[MG_SDK_BITMAP_CHUNK_WORD_FLAGS] = flags;
    graphics_put_u32(
        chunk->word + MG_SDK_BITMAP_CHUNK_WORD_DATA, primary_data_pointer);
    return 1;
}

mg_sdk_u16 mg_sdk_bitmap_pack_2bpp_word(const mg_sdk_u16 *pixels)
{
    return
        ((pixels[0] & 3) << 6) |
        ((pixels[1] & 3) << 4) |
        ((pixels[2] & 3) << 2) |
        (pixels[3] & 3) |
        ((pixels[4] & 3) << 14) |
        ((pixels[5] & 3) << 12) |
        ((pixels[6] & 3) << 10) |
        ((pixels[7] & 3) << 8);
}

mg_sdk_u16 mg_sdk_bitmap_unpack_2bpp_pixel(
    mg_sdk_u16 packed,
    mg_sdk_u16 index)
{
    static const mg_sdk_u16 shifts[8] = {
        6, 4, 2, 0, 14, 12, 10, 8
    };
    if (index >= 8) {
        return 0;
    }
    return (packed >> shifts[index]) & 3;
}
