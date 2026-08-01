#include <assert.h>

#include "mobigo_sdk/resource_bundle.h"
#include "mobigo_sdk/resource_graphics.h"

int main(void)
{
    mg_sdk_u16 auto_instances[12] = {0};
    struct mg_sdk_ui_b_record record = {{
        0xfffe, 3, 20, 0xfff0, 0x0010, 0xffa8, 0x0058,
        0, 0xffff, 0xffff, 0, 0, 0, 0
    }};
    assert(mg_sdk_bundle_auto_instance_table_words(3) == 12);
    mg_sdk_bundle_auto_instance_set_marker(auto_instances, 1, 1);
    assert(auto_instances[0] == 0 && auto_instances[1] == 0);
    assert(auto_instances[2] == 1 && auto_instances[3] == 0);
    auto_instances[6 + 4] = 0x1234;
    auto_instances[6 + 5] = 0x8000;
    assert(mg_sdk_bundle_auto_instance_read_handle(auto_instances, 3, 2) ==
           0x80001234UL);
    assert(mg_sdk_ui_b_record_delta_x(&record) == -2);
    assert(mg_sdk_ui_b_record_delta_y(&record) == 3);
    assert(mg_sdk_ui_b_record_duration(&record) == 20);
    assert(mg_sdk_ui_b_record_min_y(&record) == -16);
    assert(mg_sdk_ui_b_record_max_y(&record) == 16);
    assert(mg_sdk_ui_b_record_min_x(&record) == -88);
    assert(mg_sdk_ui_b_record_max_x(&record) == 88);
    struct mg_sdk_asset_bundle_header header = {{0}};
    struct mg_sdk_component_reference component = {{0}};
    struct mg_sdk_bitmap_descriptor bitmap = {{0}};
    struct mg_sdk_bitmap_chunk chunk = {{0}};
    struct mg_sdk_ui_b_record authored_record = {{0}};
    struct mg_sdk_component_reference authored_component = {{0}};
    struct mg_sdk_bitmap_descriptor authored_bitmap = {{0}};
    struct mg_sdk_bitmap_chunk authored_chunk = {{0}};
    const mg_sdk_u16 pixels[8] = {0, 1, 2, 3, 3, 2, 1, 0};
    mg_sdk_u16 packed;
    mg_sdk_u16 index;

    mg_sdk_bundle_write_word_pair(
        header.word, MG_SDK_ASSET_BUNDLE_WORD_UI_B_TABLE, 0x00014826UL);
    assert(
        header.word[MG_SDK_ASSET_BUNDLE_WORD_UI_B_TABLE] == 0x4826);
    assert(
        header.word[MG_SDK_ASSET_BUNDLE_WORD_UI_B_TABLE + 1] == 0x0001);
    assert(
        mg_sdk_bundle_read_word_pair(
            header.word, MG_SDK_ASSET_BUNDLE_WORD_UI_B_TABLE) ==
        0x00014826UL);
    assert(
        mg_sdk_bundle_relative_to_word_address(
            0x000e2160UL, 0x00014826UL) ==
        0x000f69a6UL);
    assert(
        mg_sdk_bundle_primary_relative(0x0001c5e0UL) ==
        0x8001c5e0UL);
    assert(
        mg_sdk_bundle_secondary_relative(0x00000100UL) ==
        0xc0000100UL);
    bitmap.word[MG_SDK_BITMAP_WORD_WIDTH] = 48;
    bitmap.word[MG_SDK_BITMAP_WORD_HEIGHT] = 32;
    bitmap.word[MG_SDK_BITMAP_WORD_FORMAT] =
        mg_sdk_bitmap_pack_format(MG_SDK_BITMAP_FORMAT_2BPP, 11, 0);
    assert(mg_sdk_bitmap_width(&bitmap) == 48);
    assert(mg_sdk_bitmap_height(&bitmap) == 32);
    assert(bitmap.word[MG_SDK_BITMAP_WORD_FORMAT] == 0x0b00);
    assert(mg_sdk_bitmap_format_code(&bitmap) == MG_SDK_BITMAP_FORMAT_2BPP);
    assert(mg_sdk_bitmap_bits_per_pixel(&bitmap) == 2);
    assert(mg_sdk_bitmap_palette_selector(&bitmap) == 11);
    assert(mg_sdk_bitmap_uses_extended_palette(&bitmap) == 0);
    assert(mg_sdk_bitmap_default_sprite_palette_index(&bitmap) == 0x01b0);
    bitmap.word[MG_SDK_BITMAP_WORD_FORMAT] =
        mg_sdk_bitmap_pack_format(MG_SDK_BITMAP_FORMAT_2BPP, 0, 1);
    assert(bitmap.word[MG_SDK_BITMAP_WORD_FORMAT] == 0x1000);
    assert(mg_sdk_bitmap_palette_selector(&bitmap) == 0);
    assert(mg_sdk_bitmap_uses_extended_palette(&bitmap) == 1);
    assert(mg_sdk_bitmap_default_sprite_palette_index(&bitmap) == 0x0300);
    bitmap.word[MG_SDK_BITMAP_WORD_FORMAT] =
        mg_sdk_bitmap_pack_format(MG_SDK_BITMAP_FORMAT_8BPP, 0, 0);
    assert(mg_sdk_bitmap_bits_per_pixel(&bitmap) == 8);
    bitmap.word[MG_SDK_BITMAP_WORD_FORMAT] = 9;
    assert(mg_sdk_bitmap_bits_per_pixel(&bitmap) == 0);
    assert(mg_sdk_rgb555_pack(31, 31, 31, 0) == 0x7fff);
    assert(mg_sdk_rgb555_pack(0, 0, 0, 1) == 0x8000);
    chunk.word[MG_SDK_BITMAP_CHUNK_WORD_DIMENSIONS] =
        mg_sdk_bitmap_pack_chunk_dimensions(16, 32);
    assert(mg_sdk_bitmap_chunk_width(&chunk) == 16);
    assert(mg_sdk_bitmap_chunk_height(&chunk) == 32);
    assert(mg_sdk_bitmap_chunk_axis_supported(16) == 1);
    assert(mg_sdk_bitmap_chunk_axis_supported(32) == 1);
    assert(mg_sdk_bitmap_chunk_axis_supported(64) == 1);
    assert(mg_sdk_bitmap_chunk_axis_supported(8) == 0);
    assert(mg_sdk_bitmap_chunk_dimensions_supported(16, 64) == 1);
    assert(mg_sdk_bitmap_chunk_dimensions_supported(8, 16) == 0);
    mg_sdk_ui_b_record_build(
        &authored_record, 2, -3, 12, -8, 8, -16, 16,
        0xffffffffUL, 0x120, 0x180);
    assert(mg_sdk_ui_b_record_delta_x(&authored_record) == 2);
    assert(mg_sdk_ui_b_record_delta_y(&authored_record) == -3);
    assert(mg_sdk_ui_b_record_duration(&authored_record) == 12);
    assert(authored_record.word[8] == 0xffff);
    assert(authored_record.word[9] == 0xffff);
    assert(mg_sdk_bundle_read_word_pair(authored_record.word, 10) == 0x120);
    assert(mg_sdk_bundle_read_word_pair(authored_record.word, 12) == 0x180);
    mg_sdk_component_build(&authored_component, -4, 5, 0x220);
    assert(mg_sdk_component_x_offset(&authored_component) == -4);
    assert(mg_sdk_component_y_offset(&authored_component) == 5);
    assert(mg_sdk_bundle_read_word_pair(authored_component.word, 2) == 0x220);
    mg_sdk_bitmap_build(
        &authored_bitmap,
        mg_sdk_bitmap_pack_format(MG_SDK_BITMAP_FORMAT_2BPP, 1, 0),
        32, 16, 0x300);
    assert(mg_sdk_bitmap_width(&authored_bitmap) == 32);
    assert(mg_sdk_bitmap_height(&authored_bitmap) == 16);
    assert(mg_sdk_bitmap_palette_selector(&authored_bitmap) == 1);
    assert(mg_sdk_bundle_read_word_pair(authored_bitmap.word, 4) == 0x300);
    assert(mg_sdk_bitmap_chunk_build(
        &authored_chunk, 32, 16, 0,
        MG_SDK_BUNDLE_PRIMARY_RELATIVE_TAG + 0x400));
    assert(mg_sdk_bitmap_chunk_width(&authored_chunk) == 32);
    assert(mg_sdk_bitmap_chunk_height(&authored_chunk) == 16);
    assert(!mg_sdk_bitmap_chunk_build(
        &authored_chunk, 8, 8, 0, MG_SDK_BUNDLE_PRIMARY_RELATIVE_TAG));
    component.word[MG_SDK_COMPONENT_WORD_X_OFFSET] = (mg_sdk_u16)-20;
    component.word[MG_SDK_COMPONENT_WORD_Y_OFFSET] = 0;
    assert(mg_sdk_component_x_offset(&component) == -20);
    assert(mg_sdk_component_y_offset(&component) == 0);
    packed = mg_sdk_bitmap_pack_2bpp_word(pixels);
    assert(packed == 0xe41b);
    for (index = 0; index < 8; ++index) {
        assert(mg_sdk_bitmap_unpack_2bpp_pixel(packed, index) == pixels[index]);
    }
    assert(mg_sdk_bitmap_unpack_2bpp_pixel(packed, 8) == 0);
    return 0;
}
