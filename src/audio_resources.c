#include "mobigo_sdk/audio_resources.h"

static void put_u32(mg_sdk_u16 *words, mg_sdk_u32 value)
{
    words[0] = (mg_sdk_u16)value;
    words[1] = (mg_sdk_u16)(value >> 16);
}

static mg_sdk_u32 get_u32(const mg_sdk_u16 *words)
{
    return (mg_sdk_u32)words[0] | ((mg_sdk_u32)words[1] << 16);
}

static int m_write_word(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 value)
{
    if (writer == 0 || writer->word == 0 || writer->count >= writer->capacity) {
        return 0;
    }
    writer->word[writer->count++] = value;
    return 1;
}

static int m_has_capacity(
    const struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 required_words)
{
    if (writer == 0 || writer->word == 0 || writer->count > writer->capacity) {
        return 0;
    }
    return required_words <= (mg_sdk_u16)(writer->capacity - writer->count);
}

void mg_sdk_audio_prepare_m_header(
    mg_sdk_u16 *record_words,
    mg_sdk_u16 payload_word_count)
{
    mg_sdk_u16 index;
    if (record_words == 0) {
        return;
    }
    for (index = 0; index < MG_SDK_AUDIO_M_HEADER_WORDS; ++index) {
        record_words[index] = 0;
    }
    record_words[MG_SDK_AUDIO_M_WORD_CLASS] = MG_SDK_AUDIO_RESOURCE_CLASS_M;
    put_u32(
        record_words + MG_SDK_AUDIO_M_WORD_BYTE_LENGTH_LO,
        (mg_sdk_u32)payload_word_count * 2);
    record_words[MG_SDK_AUDIO_M_WORD_VERSION] = 2;
}

void mg_sdk_audio_m_writer_init(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 *stream_words,
    mg_sdk_u16 capacity_words)
{
    if (writer == 0) {
        return;
    }
    writer->word = stream_words;
    writer->capacity = capacity_words;
    writer->count = 0;
}

int mg_sdk_audio_m_write_marker(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 value)
{
    return m_write_word(
        writer,
        MG_SDK_AUDIO_M_EVENT_MARKER | (value & 0x00ff));
}

int mg_sdk_audio_m_write_program_change(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 channel,
    mg_sdk_u16 program)
{
    return m_write_word(
        writer,
        MG_SDK_AUDIO_M_EVENT_PROGRAM_CHANGE |
            ((channel & 0x000f) << 8) |
            (program & 0x00ff));
}

int mg_sdk_audio_m_write_control_change(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 channel,
    mg_sdk_u16 controller,
    mg_sdk_u16 value)
{
    if (!m_has_capacity(writer, 2)) {
        return 0;
    }
    if (!m_write_word(
            writer,
            MG_SDK_AUDIO_M_EVENT_CONTROL_CHANGE |
                ((channel & 0x000f) << 8) |
                (controller & 0x00ff))) {
        return 0;
    }
    return m_write_word(writer, value & 0x00ff);
}

int mg_sdk_audio_m_write_skip_word(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 skipped_word)
{
    if (!m_has_capacity(writer, 2)) {
        return 0;
    }
    if (!m_write_word(writer, MG_SDK_AUDIO_M_EVENT_SKIP_WORD)) {
        return 0;
    }
    return m_write_word(writer, skipped_word);
}

int mg_sdk_audio_m_write_aux_cb(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 channel,
    mg_sdk_u16 control_word,
    const mg_sdk_u16 *block_words,
    mg_sdk_u16 block_word_count)
{
    mg_sdk_u16 index;

    if (block_word_count > 0x00ff ||
        (block_word_count != 0 && block_words == 0)) {
        return 0;
    }
    if (!m_has_capacity(writer, (mg_sdk_u16)(2 + block_word_count))) {
        return 0;
    }
    if (!m_write_word(
            writer,
            MG_SDK_AUDIO_M_EVENT_AUX_BLOCK_CONTROL |
                ((channel & 0x000f) << 8) |
                block_word_count)) {
        return 0;
    }
    if (!m_write_word(writer, control_word)) {
        return 0;
    }
    for (index = 0; index < block_word_count; ++index) {
        if (!m_write_word(writer, block_words[index])) {
            return 0;
        }
    }
    return 1;
}

int mg_sdk_audio_m_write_aux(
    struct mg_sdk_audio_m_stream_writer *writer,
    const mg_sdk_u16 *block_words,
    mg_sdk_u16 block_word_count)
{
    mg_sdk_u16 index;

    if (block_word_count > 0x00ff ||
        (block_word_count != 0 && block_words == 0)) {
        return 0;
    }
    if (!m_has_capacity(writer, (mg_sdk_u16)(1 + block_word_count))) {
        return 0;
    }
    if (!m_write_word(
            writer,
            MG_SDK_AUDIO_M_EVENT_AUX_BLOCK | block_word_count)) {
        return 0;
    }
    for (index = 0; index < block_word_count; ++index) {
        if (!m_write_word(writer, block_words[index])) {
            return 0;
        }
    }
    return 1;
}

int mg_sdk_audio_m_write_note(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 channel,
    mg_sdk_u16 note,
    mg_sdk_u16 velocity,
    mg_sdk_u16 duration)
{
    if (!m_has_capacity(writer, 3)) {
        return 0;
    }
    if (!m_write_word(writer, channel & 0x000f)) {
        return 0;
    }
    if (!m_write_word(
            writer,
            ((note & 0x007f) << 8) | (velocity & 0x007f))) {
        return 0;
    }
    return m_write_word(writer, duration);
}

int mg_sdk_audio_m_write_wait(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 ticks)
{
    if (ticks <= 0x07ff) {
        return m_write_word(writer, MG_SDK_AUDIO_M_EVENT_WAIT | ticks);
    }
    if (!m_has_capacity(writer, 2)) {
        return 0;
    }
    if (!m_write_word(
            writer,
            MG_SDK_AUDIO_M_EVENT_WAIT | 0x0800 | (ticks & 0x07ff))) {
        return 0;
    }
    return m_write_word(writer, (ticks >> 11) & 0x0007);
}

int mg_sdk_audio_m_write_end(
    struct mg_sdk_audio_m_stream_writer *writer)
{
    return m_write_word(writer, MG_SDK_AUDIO_M_EVENT_END);
}

static int pcm8_zone_spec_is_valid(
    const struct mg_sdk_audio_pcm8_zone_spec *zone)
{
    if (zone == 0) {
        return 0;
    }
    if (zone->root_key > 0x007f || zone->upper_key > 0x007f) {
        return 0;
    }
    if (zone->root_key > zone->upper_key || zone->sample_rate == 0) {
        return 0;
    }
    return 1;
}

static int pcm8_percussion_spec_is_valid(
    const struct mg_sdk_audio_pcm8_percussion_spec *percussion)
{
    if (percussion == 0 || percussion->note > 0x007f ||
        percussion->sample_rate == 0) {
        return 0;
    }
    return 1;
}

static void prepare_pcm8_patch_zone(
    struct mg_sdk_audio_patch_zone *zone,
    const struct mg_sdk_audio_pcm8_zone_spec *spec)
{
    mg_sdk_u16 index;

    for (index = 0; index < MG_SDK_AUDIO_PATCH_ZONE_WORDS; ++index) {
        zone->word[index] = 0;
    }
    put_u32(
        zone->word + MG_SDK_AUDIO_PATCH_WORD_ROOT_AND_UPPER_KEY,
        ((mg_sdk_u32)(spec->upper_key & 0x007f) << 8) |
            (spec->root_key & 0x007f));
    put_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_CONTROL, 0x64400602UL);
    put_u32(
        zone->word + MG_SDK_AUDIO_PATCH_WORD_ENVELOPE_BYTE_OFFSET,
        (spec->envelope_word_offset + MG_SDK_AUDIO_PATCH_ADDRESS_BIAS_WORDS) * 2);
    put_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_LEVEL_PAIR, 0x00007f7fUL);
    zone->word[MG_SDK_AUDIO_PATCH_WORD_SPF_TAG + 0] = 0x5053;
    zone->word[MG_SDK_AUDIO_PATCH_WORD_SPF_TAG + 1] = 0x3246;
    zone->word[MG_SDK_AUDIO_PATCH_WORD_SPF_TAG + 2] = 0x4c41;
    zone->word[MG_SDK_AUDIO_PATCH_WORD_SPF_TAG + 3] = 0x0050;
    put_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_SIGNATURE_A, 0x5f403969UL);
    put_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_SIGNATURE_B, 0x5f4039faUL);
    put_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_SAMPLE_RATE, spec->sample_rate);
    put_u32(
        zone->word + MG_SDK_AUDIO_PATCH_WORD_LOOP_BIASED_WORD_OFFSET,
        spec->loop_word_offset + MG_SDK_AUDIO_PATCH_ADDRESS_BIAS_WORDS);

    /*
     * Retail duplicates root/upper key into the upper bytes here and uses low
     * byte d4/d5 for its compressed path. A zero low byte selects PCM8.
     */
    put_u32(
        zone->word + MG_SDK_AUDIO_PATCH_WORD_FORMAT_AND_KEY_COPY,
        ((mg_sdk_u32)(spec->upper_key & 0x007f) << 16) |
            ((mg_sdk_u32)(spec->root_key & 0x007f) << 8));
    put_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_TRAILING_CONTROL, 0x00000602UL);
    put_u32(
        zone->word + MG_SDK_AUDIO_PATCH_WORD_SAMPLE_BYTE_OFFSET,
        spec->sample_byte_offset);
}

mg_sdk_u16 mg_sdk_audio_pcm8_bank_words(
    const struct mg_sdk_audio_pcm8_patch_bank_spec *bank)
{
    mg_sdk_u16 program_index;
    mg_sdk_u16 zone_index;
    mg_sdk_u16 other_index;
    mg_sdk_u16 percussion_index;
    mg_sdk_u32 total_zones;
    mg_sdk_u32 words;

    if (bank == 0 ||
        (bank->program_count == 0 && bank->percussion_count == 0) ||
        (bank->program_count != 0 && bank->program == 0) ||
        (bank->percussion_count != 0 && bank->percussion == 0)) {
        return 0;
    }
    total_zones = 0;
    for (program_index = 0; program_index < bank->program_count; ++program_index) {
        const struct mg_sdk_audio_pcm8_program_spec *program =
            bank->program + program_index;
        if (program->program > 0x007f ||
            program->zone_count == 0 || program->zone == 0) {
            return 0;
        }
        for (other_index = 0; other_index < program_index; ++other_index) {
            if (bank->program[other_index].program == program->program) {
                return 0;
            }
        }
        for (zone_index = 0; zone_index < program->zone_count; ++zone_index) {
            if (!pcm8_zone_spec_is_valid(program->zone + zone_index)) {
                return 0;
            }
            if (zone_index != 0 &&
                program->zone[zone_index - 1].upper_key >=
                    program->zone[zone_index].upper_key) {
                return 0;
            }
            total_zones++;
        }
    }

    for (percussion_index = 0;
         percussion_index < bank->percussion_count;
         ++percussion_index) {
        const struct mg_sdk_audio_pcm8_percussion_spec *percussion =
            bank->percussion + percussion_index;
        if (!pcm8_percussion_spec_is_valid(percussion)) {
            return 0;
        }
        for (other_index = 0; other_index < percussion_index; ++other_index) {
            if (bank->percussion[other_index].note == percussion->note) {
                return 0;
            }
        }
    }

    words = 14UL +
        (mg_sdk_u32)bank->program_count * 10UL +
        total_zones * 36UL +
        (mg_sdk_u32)bank->percussion_count * 46UL;
    if (words > 0xffffUL) {
        return 0;
    }
    return (mg_sdk_u16)words;
}

mg_sdk_u16 mg_sdk_audio_build_pcm8_bank(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 capacity_words,
    mg_sdk_u32 layout_address,
    const struct mg_sdk_audio_pcm8_patch_bank_spec *bank)
{
    mg_sdk_u16 required_words;
    mg_sdk_u16 index;
    mg_sdk_u16 program_index;
    mg_sdk_u16 zone_index;
    mg_sdk_u16 percussion_index;
    mg_sdk_u16 directory_word;
    mg_sdk_u16 percussion_directory_word;
    mg_sdk_u16 group_base_word;
    mg_sdk_u16 data_word;

    required_words = mg_sdk_audio_pcm8_bank_words(bank);
    if (patch_root == 0 || required_words == 0 ||
        capacity_words < required_words) {
        return 0;
    }
    for (index = 0; index < required_words; ++index) {
        patch_root[index] = 0;
    }

    put_u32(patch_root + 2, layout_address);
    put_u32(patch_root + 10, bank->program_count);
    directory_word = 12;
    percussion_directory_word = 14 + bank->program_count * 6;
    put_u32(
        patch_root + 12 + bank->program_count * 6,
        bank->percussion_count);
    group_base_word =
        14 + (bank->program_count + bank->percussion_count) * 6;
    data_word = group_base_word;

    for (program_index = 0; program_index < bank->program_count; ++program_index) {
        const struct mg_sdk_audio_pcm8_program_spec *program =
            bank->program + program_index;
        mg_sdk_u16 group_words =
            MG_SDK_AUDIO_PATCH_GROUP_PREFIX_WORDS +
            program->zone_count *
                (MG_SDK_AUDIO_PATCH_GROUP_OFFSET_WORDS +
                 MG_SDK_AUDIO_PATCH_ZONE_WORDS);
        mg_sdk_u16 *group = patch_root + data_word;
        mg_sdk_u16 zone_table_word =
            MG_SDK_AUDIO_PATCH_GROUP_PREFIX_WORDS +
            program->zone_count * MG_SDK_AUDIO_PATCH_GROUP_OFFSET_WORDS;

        put_u32(patch_root + directory_word + 0, program->program);
        put_u32(
            patch_root + directory_word + 2,
            (mg_sdk_u32)(data_word - group_base_word) * 2);
        put_u32(
            patch_root + directory_word + 4,
            (mg_sdk_u32)group_words * 2);
        directory_word += 6;

        put_u32(group + 0, program->zone_count);
        put_u32(group + 2, (mg_sdk_u32)zone_table_word * 2);
        for (zone_index = 0; zone_index < program->zone_count; ++zone_index) {
            struct mg_sdk_audio_patch_zone *zone =
                (struct mg_sdk_audio_patch_zone *)(
                    group + zone_table_word +
                    zone_index * MG_SDK_AUDIO_PATCH_ZONE_WORDS);
            put_u32(
                group + MG_SDK_AUDIO_PATCH_GROUP_PREFIX_WORDS +
                    zone_index * MG_SDK_AUDIO_PATCH_GROUP_OFFSET_WORDS,
                (mg_sdk_u32)zone_index * MG_SDK_AUDIO_PATCH_ZONE_WORDS * 2);
            prepare_pcm8_patch_zone(zone, program->zone + zone_index);
        }
        data_word += group_words;
    }

    for (percussion_index = 0;
         percussion_index < bank->percussion_count;
         ++percussion_index) {
        const struct mg_sdk_audio_pcm8_percussion_spec *percussion =
            bank->percussion + percussion_index;
        struct mg_sdk_audio_pcm8_zone_spec zone_spec;
        mg_sdk_u16 *group = patch_root + data_word;
        struct mg_sdk_audio_patch_zone *zone =
            (struct mg_sdk_audio_patch_zone *)(group + 6);

        put_u32(
            patch_root + percussion_directory_word + 0,
            percussion->note);
        put_u32(
            patch_root + percussion_directory_word + 2,
            (mg_sdk_u32)(data_word - group_base_word) * 2);
        put_u32(patch_root + percussion_directory_word + 4, 80);
        percussion_directory_word += 6;

        put_u32(group + 0, 1);
        put_u32(group + 2, 12);
        put_u32(group + 4, 0);
        zone_spec.root_key = percussion->note;
        zone_spec.upper_key = percussion->note;
        zone_spec.sample_rate = percussion->sample_rate;
        zone_spec.sample_byte_offset = percussion->sample_byte_offset;
        zone_spec.loop_word_offset = percussion->loop_word_offset;
        zone_spec.envelope_word_offset = percussion->envelope_word_offset;
        prepare_pcm8_patch_zone(zone, &zone_spec);
        data_word += 40;
    }
    return required_words;
}

static struct mg_sdk_audio_patch_zone *patch_zone_from_entry(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 group_base_word,
    const mg_sdk_u16 *directory_entry,
    mg_sdk_u16 zone_index)
{
    mg_sdk_u32 group_byte_offset;
    mg_sdk_u16 *group;
    mg_sdk_u32 zone_count;
    mg_sdk_u32 zone_table_byte_offset;
    mg_sdk_u32 zone_byte_offset;

    group_byte_offset = get_u32(directory_entry + 2);
    if ((group_byte_offset & 1) != 0) {
        return 0;
    }
    group = patch_root + group_base_word + (mg_sdk_u16)(group_byte_offset >> 1);
    zone_count = get_u32(group + 0);
    if (zone_index >= zone_count) {
        return 0;
    }
    zone_table_byte_offset = get_u32(group + 2);
    zone_byte_offset = get_u32(group + 4 + zone_index * 2);
    if (((zone_table_byte_offset | zone_byte_offset) & 1) != 0) {
        return 0;
    }
    return (struct mg_sdk_audio_patch_zone *)(
        group + (mg_sdk_u16)(zone_table_byte_offset >> 1) +
        (mg_sdk_u16)(zone_byte_offset >> 1));
}

static int patch_zone_set_format(
    struct mg_sdk_audio_patch_zone *zone,
    mg_sdk_u16 format_byte)
{
    if (zone == 0 || format_byte > 0x00ff) {
        return 0;
    }
    zone->word[MG_SDK_AUDIO_PATCH_WORD_FORMAT_AND_KEY_COPY] =
        (zone->word[MG_SDK_AUDIO_PATCH_WORD_FORMAT_AND_KEY_COPY] & 0xff00) |
        format_byte;
    return 1;
}

int mg_sdk_audio_patch_prog_fmt(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 program,
    mg_sdk_u16 zone_index,
    mg_sdk_u16 format_byte)
{
    mg_sdk_u32 program_count;
    mg_sdk_u32 percussion_count;
    mg_sdk_u16 group_base_word;
    mg_sdk_u16 index;

    if (patch_root == 0 || program > 0x007f || format_byte > 0x00ff) {
        return 0;
    }
    program_count = get_u32(patch_root + 10);
    if (program_count > 0x007f) {
        return 0;
    }
    percussion_count = get_u32(patch_root + 12 + (mg_sdk_u16)program_count * 6);
    if (percussion_count > 0x007f) {
        return 0;
    }
    group_base_word = 14 +
        ((mg_sdk_u16)program_count + (mg_sdk_u16)percussion_count) * 6;
    for (index = 0; index < (mg_sdk_u16)program_count; ++index) {
        mg_sdk_u16 *entry = patch_root + 12 + index * 6;
        if (get_u32(entry) == program) {
            return patch_zone_set_format(
                patch_zone_from_entry(
                    patch_root, group_base_word, entry, zone_index),
                format_byte);
        }
    }
    return 0;
}

int mg_sdk_audio_patch_drum_fmt(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 note,
    mg_sdk_u16 format_byte)
{
    mg_sdk_u32 program_count;
    mg_sdk_u32 percussion_count;
    mg_sdk_u16 percussion_directory_word;
    mg_sdk_u16 group_base_word;
    mg_sdk_u16 index;

    if (patch_root == 0 || note > 0x007f || format_byte > 0x00ff) {
        return 0;
    }
    program_count = get_u32(patch_root + 10);
    if (program_count > 0x007f) {
        return 0;
    }
    percussion_directory_word = 14 + (mg_sdk_u16)program_count * 6;
    percussion_count = get_u32(patch_root + percussion_directory_word - 2);
    if (percussion_count > 0x007f) {
        return 0;
    }
    group_base_word = 14 +
        ((mg_sdk_u16)program_count + (mg_sdk_u16)percussion_count) * 6;
    for (index = 0; index < (mg_sdk_u16)percussion_count; ++index) {
        mg_sdk_u16 *entry = patch_root + percussion_directory_word + index * 6;
        if (get_u32(entry) == note) {
            return patch_zone_set_format(
                patch_zone_from_entry(patch_root, group_base_word, entry, 0),
                format_byte);
        }
    }
    return 0;
}

mg_sdk_u16 mg_sdk_audio_pcm8_root_words(
    const struct mg_sdk_audio_pcm8_program_spec *programs,
    mg_sdk_u16 program_count)
{
    struct mg_sdk_audio_pcm8_patch_bank_spec bank;
    bank.program = programs;
    bank.program_count = program_count;
    bank.percussion = 0;
    bank.percussion_count = 0;
    return mg_sdk_audio_pcm8_bank_words(&bank);
}

mg_sdk_u16 mg_sdk_audio_build_pcm8_root(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 capacity_words,
    mg_sdk_u32 layout_address,
    const struct mg_sdk_audio_pcm8_program_spec *programs,
    mg_sdk_u16 program_count)
{
    struct mg_sdk_audio_pcm8_patch_bank_spec bank;
    bank.program = programs;
    bank.program_count = program_count;
    bank.percussion = 0;
    bank.percussion_count = 0;
    return mg_sdk_audio_build_pcm8_bank(
        patch_root, capacity_words, layout_address, &bank);
}

void mg_sdk_audio_pcm8_single_root(
    mg_sdk_u16 *patch_root,
    mg_sdk_u32 layout_address,
    mg_sdk_u16 program,
    mg_sdk_u16 root_key,
    mg_sdk_u16 upper_key,
    mg_sdk_u32 sample_rate,
    mg_sdk_u32 sample_byte_offset,
    mg_sdk_u32 loop_word_offset,
    mg_sdk_u32 envelope_word_offset)
{
    struct mg_sdk_audio_pcm8_zone_spec zone;
    struct mg_sdk_audio_pcm8_program_spec program_spec;

    zone.root_key = root_key;
    zone.upper_key = upper_key;
    zone.sample_rate = sample_rate;
    zone.sample_byte_offset = sample_byte_offset;
    zone.loop_word_offset = loop_word_offset;
    zone.envelope_word_offset = envelope_word_offset;
    program_spec.program = program;
    program_spec.zone = &zone;
    program_spec.zone_count = 1;
    mg_sdk_audio_build_pcm8_root(
        patch_root,
        MG_SDK_AUDIO_PATCH_SINGLE_PROGRAM_WORDS,
        layout_address,
        &program_spec,
        1);
}

void mg_sdk_audio_prepare_hold_envelope(
    mg_sdk_u16 *envelope_words,
    mg_sdk_u16 hold_ticks)
{
    if (envelope_words == 0) {
        return;
    }
    envelope_words[0] = 0x7f7f;
    envelope_words[1] = hold_ticks & 0x00ff;
}

void mg_sdk_audio_prepare_w_pcm8(
    struct mg_sdk_audio_w_record *record,
    mg_sdk_u32 byte_length,
    mg_sdk_u32 sample_rate,
    mg_sdk_u32 sample_count,
    mg_sdk_u32 data_byte_offset)
{
    mg_sdk_u16 index;

    if (record == 0) {
        return;
    }
    for (index = 0; index < MG_SDK_AUDIO_W_RECORD_WORDS; ++index) {
        record->word[index] = 0;
    }
    record->word[MG_SDK_AUDIO_W_WORD_CLASS] = MG_SDK_AUDIO_RESOURCE_CLASS_W;
    put_u32(
        record->word + MG_SDK_AUDIO_W_WORD_BYTE_LENGTH_LO,
        byte_length);
    record->word[MG_SDK_AUDIO_W_WORD_VERSION] = 2;
    record->word[MG_SDK_AUDIO_W_WORD_RELOCATION_STATE] = 0;

    /* Packed little-endian words for the eight-byte tag "SPF2ALP\0". */
    record->word[MG_SDK_AUDIO_W_WORD_SPF_TAG + 0] = 0x5053;
    record->word[MG_SDK_AUDIO_W_WORD_SPF_TAG + 1] = 0x3246;
    record->word[MG_SDK_AUDIO_W_WORD_SPF_TAG + 2] = 0x4c41;
    record->word[MG_SDK_AUDIO_W_WORD_SPF_TAG + 3] = 0x0050;

    put_u32(
        record->word + MG_SDK_AUDIO_W_WORD_SAMPLE_RATE_LO,
        sample_rate);
    put_u32(
        record->word + MG_SDK_AUDIO_W_WORD_SAMPLE_COUNT_LO,
        sample_count);
    record->word[MG_SDK_AUDIO_W_WORD_FORMAT_FLAGS] =
        MG_SDK_AUDIO_W_FORMAT_PCM8;

    /* Retail W records use these invariant mixer/control defaults. */
    record->word[MG_SDK_AUDIO_W_WORD_CONTROL_27] = 0x007f;
    record->word[MG_SDK_AUDIO_W_WORD_CONTROL_28] = 0x7f00;
    record->word[MG_SDK_AUDIO_W_WORD_CONTROL_29] = 0x6440;
    put_u32(
        record->word + MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_LO,
        data_byte_offset);
}

void mg_sdk_audio_w_adpcm36(
    struct mg_sdk_audio_w_record *record,
    mg_sdk_u32 byte_length,
    mg_sdk_u32 sample_rate,
    mg_sdk_u32 sample_count,
    mg_sdk_u32 data_byte_offset)
{
    mg_sdk_audio_prepare_w_pcm8(
        record,
        byte_length,
        sample_rate,
        sample_count,
        data_byte_offset);
    if (record != 0) {
        record->word[MG_SDK_AUDIO_W_WORD_FORMAT_FLAGS] =
            MG_SDK_AUDIO_W_FORMAT_ADPCM36;
    }
}

mg_sdk_u16 mg_sdk_adpcm36_encode_frame(
    mg_sdk_u16 *output_words,
    const mg_sdk_s16 *samples)
{
    mg_sdk_u16 shift;
    mg_sdk_u16 index;
    mg_sdk_u16 word_index;
    int shift_candidate;
    mg_sdk_s16 sample;
    int step;
    int magnitude;
    int quantized;
    int fits;

    if (output_words == 0 || samples == 0) {
        return 0xffff;
    }

    shift = 0;
    for (shift_candidate = 12; shift_candidate >= 0; --shift_candidate) {
        step = 1 << (12 - shift_candidate);
        fits = 1;
        for (word_index = 0;
             word_index < MG_SDK_ADPCM36_SAMPLES_PER_FRAME;
             ++word_index) {
            sample = samples[word_index];
            if ((sample >= 0 && sample > 7 * step) ||
                (sample < 0 && sample < -8 * step)) {
                fits = 0;
                break;
            }
        }
        if (fits) {
            shift = (mg_sdk_u16)shift_candidate;
            break;
        }
    }

    output_words[0] = shift;
    step = 1 << (12 - shift);
    for (word_index = 0; word_index < MG_SDK_ADPCM36_DATA_WORDS; ++word_index) {
        mg_sdk_u16 packed = 0;
        for (index = 0; index < 4; ++index) {
            sample = samples[word_index * 4 + index];
            if (sample < 0) {
                magnitude = -(int)sample;
                quantized = -((magnitude + step / 2) / step);
                if (quantized < -8) {
                    quantized = -8;
                }
            } else {
                quantized = ((int)sample + step / 2) / step;
                if (quantized > 7) {
                    quantized = 7;
                }
            }
            packed |= (mg_sdk_u16)(quantized & 0x000f) << (index * 4);
        }
        output_words[1 + word_index] = packed;
    }
    return shift;
}

void mg_sdk_adpcm36_finish(mg_sdk_u16 *output_words)
{
    if (output_words == 0) {
        return;
    }
    output_words[0] = 0;
    output_words[1] = 0xffff;
}

void mg_sdk_audio_prepare_s_sequence(
    mg_sdk_u16 *record_words,
    const mg_sdk_u16 *child_resource_ids,
    mg_sdk_u16 child_count)
{
    mg_sdk_u16 index;
    mg_sdk_u16 total_words;

    if (record_words == 0 || (child_count != 0 && child_resource_ids == 0)) {
        return;
    }
    total_words = MG_SDK_AUDIO_S_HEADER_WORDS + (child_count + 1) * 2;
    for (index = 0; index < total_words; ++index) {
        record_words[index] = 0;
    }
    record_words[MG_SDK_AUDIO_S_WORD_CLASS] = MG_SDK_AUDIO_RESOURCE_CLASS_S;
    put_u32(
        record_words + MG_SDK_AUDIO_S_WORD_BYTE_LENGTH_LO,
        (mg_sdk_u32)(child_count + 1) * 4);
    record_words[MG_SDK_AUDIO_S_WORD_VERSION] = 2;
    record_words[MG_SDK_AUDIO_S_WORD_RELOCATION_STATE] = 0;
    put_u32(record_words + MG_SDK_AUDIO_S_WORD_SEQUENCE_OFFSET_LO, 0);

    for (index = 0; index < child_count; ++index) {
        put_u32(
            record_words + MG_SDK_AUDIO_S_WORD_SEQUENCE + index * 2,
            MG_SDK_AUDIO_LOCAL_RESOURCE_TAG |
                (child_resource_ids[index] & 0x0fff));
    }
    put_u32(
        record_words + MG_SDK_AUDIO_S_WORD_SEQUENCE + child_count * 2,
        0xffffffffUL);
}

void mg_sdk_audio_prepare_root(
    mg_sdk_u16 *root,
    mg_sdk_u16 m_count,
    mg_sdk_u16 w_count,
    mg_sdk_u16 s_count,
    const mg_sdk_u32 *resource_addresses,
    mg_sdk_u32 layout_address)
{
    mg_sdk_u16 index;
    mg_sdk_u16 resource_count;
    mg_sdk_u16 total_words;

    if (root == 0) {
        return;
    }
    resource_count = m_count + w_count + s_count;
    if (resource_count != 0 && resource_addresses == 0) {
        return;
    }
    total_words = 6 + resource_count * 2 + 2;
    for (index = 0; index < total_words; ++index) {
        root[index] = 0;
    }
    put_u32(root + 0, m_count);
    put_u32(root + 2, w_count);
    put_u32(root + 4, s_count);
    for (index = 0; index < resource_count; ++index) {
        put_u32(root + 6 + index * 2, resource_addresses[index]);
    }
    put_u32(root + 6 + resource_count * 2, layout_address);
}

void mg_sdk_audio_prepare_single_w_root(
    mg_sdk_u16 *root,
    mg_sdk_u32 w_record_address,
    mg_sdk_u32 layout_address)
{
    mg_sdk_u32 resources[1];
    resources[0] = w_record_address;
    mg_sdk_audio_prepare_root(root, 0, 1, 0, resources, layout_address);
}

void mg_sdk_audio_prepare_wave_layout(
    mg_sdk_u16 *layout,
    mg_sdk_u32 wave_base_word_address,
    mg_sdk_u32 wave_region_words)
{
    if (layout == 0) {
        return;
    }
    put_u32(layout + 0, wave_base_word_address);
    put_u32(layout + 2, wave_region_words);
}

void mg_sdk_audio_prepare_empty_patch_root(
    mg_sdk_u16 *patch_root,
    mg_sdk_u32 layout_address)
{
    mg_sdk_u16 index;
    if (patch_root == 0) {
        return;
    }
    for (index = 0; index < 14; ++index) {
        patch_root[index] = 0;
    }
    put_u32(patch_root + 2, layout_address);
}
