#include "mobigo_sdk/resource_bundle.h"

mg_sdk_u32 mg_sdk_bundle_read_word_pair(
    const mg_sdk_u16 *words,
    mg_sdk_u16 word_offset)
{
    mg_sdk_u32 low = words[word_offset];
    mg_sdk_u32 high = words[word_offset + 1];
    return low | (high << 16);
}

void mg_sdk_bundle_write_word_pair(
    mg_sdk_u16 *words,
    mg_sdk_u16 word_offset,
    mg_sdk_u32 value)
{
    words[word_offset] = (mg_sdk_u16)value;
    words[word_offset + 1] = (mg_sdk_u16)(value >> 16);
}

mg_sdk_u32 mg_sdk_bundle_relative_to_word_address(
    mg_sdk_u32 header_word_address,
    mg_sdk_u32 relative_word_pointer)
{
    return header_word_address +
        (mg_sdk_u32)MG_SDK_ASSET_BUNDLE_HEADER_WORDS +
        relative_word_pointer;
}

mg_sdk_u32 mg_sdk_bundle_primary_relative(mg_sdk_u32 word_offset)
{
    return MG_SDK_BUNDLE_PRIMARY_RELATIVE_TAG |
        (word_offset & MG_SDK_BUNDLE_PRIMARY_OFFSET_MASK);
}

mg_sdk_u32 mg_sdk_bundle_secondary_relative(mg_sdk_u32 word_offset)
{
    return MG_SDK_BUNDLE_SECONDARY_RELATIVE_TAG |
        (word_offset & MG_SDK_BUNDLE_SECONDARY_OFFSET_MASK);
}

mg_sdk_u16 mg_sdk_bundle_auto_instance_table_words(
    mg_sdk_u16 descriptor_count)
{
    return (mg_sdk_u16)(descriptor_count * 4u);
}

void mg_sdk_bundle_auto_instance_set_marker(
    mg_sdk_u16 *table,
    mg_sdk_u16 descriptor_index,
    mg_sdk_u32 marker)
{
    mg_sdk_bundle_write_word_pair(
        table,
        (mg_sdk_u16)(descriptor_index * 2u),
        marker);
}

mg_sdk_u32 mg_sdk_bundle_auto_instance_read_handle(
    const mg_sdk_u16 *table,
    mg_sdk_u16 descriptor_count,
    mg_sdk_u16 descriptor_index)
{
    return mg_sdk_bundle_read_word_pair(
        table,
        (mg_sdk_u16)(descriptor_count * 2u + descriptor_index * 2u));
}
