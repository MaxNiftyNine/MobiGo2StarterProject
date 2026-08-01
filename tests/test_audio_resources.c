#include <assert.h>

#include "mobigo_sdk/audio_resources.h"

static mg_sdk_u32 get_u32(const mg_sdk_u16 *words)
{
    return (mg_sdk_u32)words[0] | ((mg_sdk_u32)words[1] << 16);
}

int main(void)
{
    mg_sdk_u16 m_record[32];
    struct mg_sdk_audio_m_stream_writer writer;
    struct mg_sdk_audio_w_record record;
    struct mg_sdk_audio_w_record compressed_record;
    mg_sdk_s16 adpcm_samples[MG_SDK_ADPCM36_SAMPLES_PER_FRAME];
    mg_sdk_u16 adpcm_frame[
        MG_SDK_ADPCM36_FRAME_WORDS + MG_SDK_ADPCM36_END_WORDS];
    mg_sdk_u16 root[10];
    mg_sdk_u16 generic_root[14];
    mg_sdk_u16 s_record[16];
    mg_sdk_u16 child_ids[2] = {3, 4};
    mg_sdk_u32 addresses[3] = {0x5a20, 0x5a40, 0x5a70};
    mg_sdk_u16 layout[4];
    mg_sdk_u16 patch_root[MG_SDK_AUDIO_PATCH_SINGLE_PROGRAM_WORDS];
    mg_sdk_u16 multi_patch_root[142];
    mg_sdk_u16 envelope[2];
    mg_sdk_u16 empty_patch_root[14];
    struct mg_sdk_audio_patch_zone *zone;
    struct mg_sdk_audio_patch_zone *multi_zone;
    struct mg_sdk_audio_pcm8_zone_spec multi_zones_a[2];
    struct mg_sdk_audio_pcm8_zone_spec multi_zones_b[1];
    struct mg_sdk_audio_pcm8_program_spec multi_programs[2];
    struct mg_sdk_audio_pcm8_percussion_spec percussion[2];
    struct mg_sdk_audio_pcm8_patch_bank_spec bank;
    mg_sdk_u16 full_patch_root[234];
    mg_sdk_u16 aux_a[2] = {0x1234, 0x5678};
    mg_sdk_u16 aux_b[2] = {0x9abc, 0xdef0};
    mg_sdk_u16 short_stream[4] = {0xaaaa, 0xbbbb, 0xcccc, 0xdddd};
    mg_sdk_u16 index;

    mg_sdk_audio_m_writer_init(&writer, m_record + MG_SDK_AUDIO_M_WORD_STREAM, 22);
    assert(mg_sdk_audio_m_write_marker(&writer, 120));
    assert(mg_sdk_audio_m_write_program_change(&writer, 3, 0x38));
    assert(mg_sdk_audio_m_write_control_change(&writer, 3, 7, 100));
    assert(mg_sdk_audio_m_write_skip_word(&writer, 0xabcd));
    assert(mg_sdk_audio_m_write_aux_cb(&writer, 3, 0x4567, aux_a, 2));
    assert(mg_sdk_audio_m_write_aux(&writer, aux_b, 2));
    assert(mg_sdk_audio_m_write_note(&writer, 3, 60, 96, 24));
    assert(mg_sdk_audio_m_write_wait(&writer, 0x28));
    assert(mg_sdk_audio_m_write_wait(&writer, 0x1234));
    assert(mg_sdk_audio_m_write_end(&writer));
    assert(writer.count == 20);
    mg_sdk_audio_prepare_m_header(m_record, writer.count);
    assert(m_record[0] == MG_SDK_AUDIO_RESOURCE_CLASS_M);
    assert(get_u32(m_record + 2) == 40);
    assert(m_record[4] == 2);
    assert(m_record[10] == 0x5078);
    assert(m_record[11] == 0x4338);
    assert(m_record[12] == 0x3307);
    assert(m_record[13] == 100);
    assert(m_record[14] == 0x2000);
    assert(m_record[15] == 0xabcd);
    assert(m_record[16] == 0x7302);
    assert(m_record[17] == 0x4567);
    assert(m_record[18] == 0x1234);
    assert(m_record[19] == 0x5678);
    assert(m_record[20] == 0x8002);
    assert(m_record[21] == 0x9abc);
    assert(m_record[22] == 0xdef0);
    assert(m_record[23] == 0x0003);
    assert(m_record[24] == 0x3c60);
    assert(m_record[25] == 24);
    assert(m_record[26] == 0x1028);
    assert(m_record[27] == (0x1800 | (0x1234 & 0x07ff)));
    assert(m_record[28] == ((0x1234 >> 11) & 7));
    assert(m_record[29] == 0x6000);

    /* Multiword events are transactional when the output buffer is full. */
    mg_sdk_audio_m_writer_init(&writer, short_stream, 1);
    assert(!mg_sdk_audio_m_write_control_change(&writer, 3, 7, 100));
    assert(writer.count == 0 && short_stream[0] == 0xaaaa);
    assert(!mg_sdk_audio_m_write_skip_word(&writer, 0x1234));
    assert(writer.count == 0 && short_stream[0] == 0xaaaa);
    assert(!mg_sdk_audio_m_write_wait(&writer, 0x1234));
    assert(writer.count == 0 && short_stream[0] == 0xaaaa);

    mg_sdk_audio_m_writer_init(&writer, short_stream, 2);
    assert(!mg_sdk_audio_m_write_note(&writer, 3, 60, 96, 24));
    assert(writer.count == 0 && short_stream[0] == 0xaaaa);
    assert(!mg_sdk_audio_m_write_aux(&writer, aux_a, 2));
    assert(writer.count == 0 && short_stream[0] == 0xaaaa);

    mg_sdk_audio_m_writer_init(&writer, short_stream, 3);
    assert(!mg_sdk_audio_m_write_aux_cb(&writer, 3, 0x4567, aux_a, 2));
    assert(writer.count == 0 && short_stream[0] == 0xaaaa);

    mg_sdk_audio_prepare_single_pcm8_patch_root(
        patch_root, 0x5a40, 0, 60, 60, 4000, 0, 0, 34);
    assert(get_u32(patch_root + 2) == 0x5a40);
    assert(get_u32(patch_root + 10) == 1);
    assert(get_u32(patch_root + 12) == 0);
    assert(get_u32(patch_root + 16) == 0x50);
    assert(get_u32(patch_root + 18) == 0);
    assert(get_u32(patch_root + 20) == 1);
    assert(get_u32(patch_root + 22) == 0x0c);
    zone = (struct mg_sdk_audio_patch_zone *)(patch_root + 26);
    assert(get_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_KEY_RANGE) == 0x3c3c);
    assert(get_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_CONTROL) == 0x64400602UL);
    assert(get_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_ENVELOPE_BYTE_OFFSET) == 0x6c);
    assert(get_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_SAMPLE_RATE) == 4000);
    assert(get_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_LOOP_BIASED_WORD_OFFSET) == 0x14);
    assert(get_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_FORMAT_AND_KEY_COPY) == 0x3c3c00);
    assert(get_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_TRAILING_CONTROL) == 0x602);
    assert(get_u32(zone->word + MG_SDK_AUDIO_PATCH_WORD_SAMPLE_BYTE_OFFSET) == 0);
    mg_sdk_audio_prepare_hold_envelope(envelope, 0xff);
    assert(envelope[0] == 0x7f7f);
    assert(envelope[1] == 0x00ff);
    mg_sdk_audio_prepare_empty_patch_root(empty_patch_root, 0x5a40);
    assert(get_u32(empty_patch_root + 2) == 0x5a40);
    assert(get_u32(empty_patch_root + 10) == 0);
    assert(get_u32(empty_patch_root + 12) == 0);

    multi_zones_a[0].root_key = 48;
    multi_zones_a[0].upper_key = 60;
    multi_zones_a[0].sample_rate = 4000;
    multi_zones_a[0].sample_byte_offset = 0;
    multi_zones_a[0].loop_word_offset = 0;
    multi_zones_a[0].envelope_word_offset = 68;
    multi_zones_a[1].root_key = 72;
    multi_zones_a[1].upper_key = 127;
    multi_zones_a[1].sample_rate = 6000;
    multi_zones_a[1].sample_byte_offset = 68;
    multi_zones_a[1].loop_word_offset = 34;
    multi_zones_a[1].envelope_word_offset = 70;
    multi_zones_b[0].root_key = 60;
    multi_zones_b[0].upper_key = 127;
    multi_zones_b[0].sample_rate = 8000;
    multi_zones_b[0].sample_byte_offset = 144;
    multi_zones_b[0].loop_word_offset = 72;
    multi_zones_b[0].envelope_word_offset = 106;
    multi_programs[0].program = 2;
    multi_programs[0].zone = multi_zones_a;
    multi_programs[0].zone_count = 2;
    multi_programs[1].program = 7;
    multi_programs[1].zone = multi_zones_b;
    multi_programs[1].zone_count = 1;

    percussion[0].note = 36;
    percussion[0].sample_rate = 5000;
    percussion[0].sample_byte_offset = 216;
    percussion[0].loop_word_offset = 108;
    percussion[0].envelope_word_offset = 142;
    percussion[1].note = 42;
    percussion[1].sample_rate = 7000;
    percussion[1].sample_byte_offset = 284;
    percussion[1].loop_word_offset = 142;
    percussion[1].envelope_word_offset = 176;
    bank.program = multi_programs;
    bank.program_count = 2;
    bank.percussion = percussion;
    bank.percussion_count = 2;
    assert(mg_sdk_audio_pcm8_patch_bank_words(&bank) == 234);
    assert(mg_sdk_audio_prepare_pcm8_patch_bank(
        full_patch_root, 233, 0x5d00, &bank) == 0);
    assert(mg_sdk_audio_prepare_pcm8_patch_bank(
        full_patch_root, 234, 0x5d00, &bank) == 234);
    assert(get_u32(full_patch_root + 10) == 2);
    assert(get_u32(full_patch_root + 24) == 2);
    assert(get_u32(full_patch_root + 26) == 36);
    assert(get_u32(full_patch_root + 28) == 232);
    assert(get_u32(full_patch_root + 30) == 80);
    assert(get_u32(full_patch_root + 32) == 42);
    assert(get_u32(full_patch_root + 34) == 312);
    assert(get_u32(full_patch_root + 36) == 80);
    /* Group data begins at word 38; melodic groups consume 116 words. */
    assert(get_u32(full_patch_root + 38) == 2);
    assert(get_u32(full_patch_root + 114) == 1);
    assert(get_u32(full_patch_root + 154) == 1);
    assert(get_u32(full_patch_root + 156) == 12);
    multi_zone = (struct mg_sdk_audio_patch_zone *)(full_patch_root + 160);
    assert(get_u32(multi_zone->word +
        MG_SDK_AUDIO_PATCH_WORD_ROOT_AND_UPPER_KEY) == 0x2424);
    assert(get_u32(multi_zone->word +
        MG_SDK_AUDIO_PATCH_WORD_SAMPLE_RATE) == 5000);
    assert(get_u32(full_patch_root + 194) == 1);
    multi_zone = (struct mg_sdk_audio_patch_zone *)(full_patch_root + 200);
    assert(get_u32(multi_zone->word +
        MG_SDK_AUDIO_PATCH_WORD_ROOT_AND_UPPER_KEY) == 0x2a2a);
    assert(get_u32(multi_zone->word +
        MG_SDK_AUDIO_PATCH_WORD_SAMPLE_RATE) == 7000);
    assert(mg_sdk_audio_set_program_zone_format(
        full_patch_root, 2, 1, MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36));
    multi_zone = (struct mg_sdk_audio_patch_zone *)(full_patch_root + 80);
    assert((multi_zone->word[MG_SDK_AUDIO_PATCH_WORD_FORMAT_AND_KEY_COPY] &
        0x00ff) == MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36);
    assert(mg_sdk_audio_set_percussion_format(
        full_patch_root, 36, MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36));
    multi_zone = (struct mg_sdk_audio_patch_zone *)(full_patch_root + 160);
    assert((multi_zone->word[MG_SDK_AUDIO_PATCH_WORD_FORMAT_AND_KEY_COPY] &
        0x00ff) == MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36);
    assert(!mg_sdk_audio_set_program_zone_format(
        full_patch_root, 99, 0, MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36));
    assert(!mg_sdk_audio_set_program_zone_format(
        full_patch_root, 2, 9, MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36));
    assert(!mg_sdk_audio_set_percussion_format(
        full_patch_root, 99, MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36));
    assert(!mg_sdk_audio_set_percussion_format(full_patch_root, 36, 0x0100));
    percussion[1].note = 36;
    assert(mg_sdk_audio_pcm8_patch_bank_words(&bank) == 0);
    percussion[1].note = 42;
    assert(mg_sdk_audio_pcm8_patch_root_words(multi_programs, 2) == 142);
    assert(mg_sdk_audio_prepare_pcm8_patch_root(
        multi_patch_root, 141, 0x5c00, multi_programs, 2) == 0);
    assert(mg_sdk_audio_prepare_pcm8_patch_root(
        multi_patch_root, 142, 0x5c00, multi_programs, 2) == 142);
    assert(get_u32(multi_patch_root + 2) == 0x5c00);
    assert(get_u32(multi_patch_root + 10) == 2);
    assert(get_u32(multi_patch_root + 12) == 2);
    assert(get_u32(multi_patch_root + 14) == 0);
    assert(get_u32(multi_patch_root + 16) == 152);
    assert(get_u32(multi_patch_root + 18) == 7);
    assert(get_u32(multi_patch_root + 20) == 152);
    assert(get_u32(multi_patch_root + 22) == 80);
    assert(get_u32(multi_patch_root + 24) == 0);
    assert(get_u32(multi_patch_root + 26) == 2);
    assert(get_u32(multi_patch_root + 28) == 16);
    assert(get_u32(multi_patch_root + 30) == 0);
    assert(get_u32(multi_patch_root + 32) == 68);
    multi_zone = (struct mg_sdk_audio_patch_zone *)(multi_patch_root + 34);
    assert(get_u32(multi_zone->word +
        MG_SDK_AUDIO_PATCH_WORD_ROOT_AND_UPPER_KEY) == 0x3c30);
    multi_zone = (struct mg_sdk_audio_patch_zone *)(multi_patch_root + 68);
    assert(get_u32(multi_zone->word +
        MG_SDK_AUDIO_PATCH_WORD_ROOT_AND_UPPER_KEY) == 0x7f48);
    assert(get_u32(multi_zone->word +
        MG_SDK_AUDIO_PATCH_WORD_SAMPLE_BYTE_OFFSET) == 68);
    assert(get_u32(multi_patch_root + 102) == 1);
    assert(get_u32(multi_patch_root + 104) == 12);
    assert(get_u32(multi_patch_root + 106) == 0);
    multi_zone = (struct mg_sdk_audio_patch_zone *)(multi_patch_root + 108);
    assert(get_u32(multi_zone->word +
        MG_SDK_AUDIO_PATCH_WORD_ROOT_AND_UPPER_KEY) == 0x7f3c);

    multi_programs[1].program = 2;
    assert(mg_sdk_audio_pcm8_patch_root_words(multi_programs, 2) == 0);
    multi_programs[1].program = 7;
    multi_zones_a[1].upper_key = 60;
    assert(mg_sdk_audio_pcm8_patch_root_words(multi_programs, 2) == 0);
    multi_zones_a[1].upper_key = 127;

    mg_sdk_audio_prepare_w_pcm8(&record, 0x44, 4000, 64, 0x1234);
    assert(record.word[MG_SDK_AUDIO_W_WORD_CLASS] ==
        MG_SDK_AUDIO_RESOURCE_CLASS_W);
    assert(get_u32(record.word + MG_SDK_AUDIO_W_WORD_BYTE_LENGTH_LO) ==
        0x44);
    assert(record.word[MG_SDK_AUDIO_W_WORD_VERSION] == 2);
    assert(record.word[MG_SDK_AUDIO_W_WORD_RELOCATION_STATE] == 0);
    assert(record.word[10] == 0x5053);
    assert(record.word[11] == 0x3246);
    assert(record.word[12] == 0x4c41);
    assert(record.word[13] == 0x0050);
    assert(get_u32(record.word + MG_SDK_AUDIO_W_WORD_SAMPLE_RATE_LO) ==
        4000);
    assert(get_u32(record.word + MG_SDK_AUDIO_W_WORD_SAMPLE_COUNT_LO) ==
        64);
    assert(record.word[MG_SDK_AUDIO_W_WORD_FORMAT_FLAGS] ==
        MG_SDK_AUDIO_W_FORMAT_PCM8);
    assert(record.word[27] == 0x007f);
    assert(record.word[28] == 0x7f00);
    assert(record.word[29] == 0x6440);
    assert(get_u32(record.word + MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_LO) ==
        0x1234);

    for (index = 0; index < MG_SDK_ADPCM36_SAMPLES_PER_FRAME; ++index) {
        adpcm_samples[index] = (index & 4) ? -12288 : 12288;
    }
    assert(mg_sdk_adpcm36_encode_frame(adpcm_frame, adpcm_samples) == 1);
    assert(adpcm_frame[0] == 1);
    assert(adpcm_frame[1] == 0x6666);
    assert(adpcm_frame[2] == 0xaaaa);
    assert(adpcm_frame[7] == 0x6666);
    assert(adpcm_frame[8] == 0xaaaa);
    mg_sdk_adpcm36_finish(adpcm_frame + MG_SDK_ADPCM36_FRAME_WORDS);
    assert(adpcm_frame[9] == 0);
    assert(adpcm_frame[10] == 0xffff);
    mg_sdk_audio_prepare_w_adpcm36(
        &compressed_record,
        sizeof(adpcm_frame),
        1000,
        MG_SDK_ADPCM36_SAMPLES_PER_FRAME,
        0x40);
    assert(compressed_record.word[MG_SDK_AUDIO_W_WORD_FORMAT_FLAGS] ==
        MG_SDK_AUDIO_W_FORMAT_ADPCM36);
    assert(get_u32(
        compressed_record.word + MG_SDK_AUDIO_W_WORD_BYTE_LENGTH_LO) ==
        sizeof(adpcm_frame));
    assert(get_u32(
        compressed_record.word + MG_SDK_AUDIO_W_WORD_SAMPLE_RATE_LO) == 1000);

    mg_sdk_audio_prepare_single_w_root(root, 0x5a20, 0x5a60);
    assert(get_u32(root + 0) == 0);
    assert(get_u32(root + 2) == 1);
    assert(get_u32(root + 4) == 0);
    assert(get_u32(root + 6) == 0x5a20);
    assert(get_u32(root + 8) == 0x5a60);

    mg_sdk_audio_prepare_s_sequence(s_record, child_ids, 2);
    assert(s_record[MG_SDK_AUDIO_S_WORD_CLASS] ==
        MG_SDK_AUDIO_RESOURCE_CLASS_S);
    assert(get_u32(s_record + MG_SDK_AUDIO_S_WORD_BYTE_LENGTH_LO) == 12);
    assert(s_record[MG_SDK_AUDIO_S_WORD_VERSION] == 2);
    assert(get_u32(s_record + MG_SDK_AUDIO_S_WORD_SEQUENCE_OFFSET_LO) == 0);
    assert(get_u32(s_record + MG_SDK_AUDIO_S_WORD_SEQUENCE + 0) == 0xc003);
    assert(get_u32(s_record + MG_SDK_AUDIO_S_WORD_SEQUENCE + 2) == 0xc004);
    assert(get_u32(s_record + MG_SDK_AUDIO_S_WORD_SEQUENCE + 4) ==
        0xffffffffUL);

    mg_sdk_audio_prepare_root(
        generic_root, 0, 2, 1, addresses, 0x5a60);
    assert(get_u32(generic_root + 0) == 0);
    assert(get_u32(generic_root + 2) == 2);
    assert(get_u32(generic_root + 4) == 1);
    assert(get_u32(generic_root + 6) == 0x5a20);
    assert(get_u32(generic_root + 8) == 0x5a40);
    assert(get_u32(generic_root + 10) == 0x5a70);
    assert(get_u32(generic_root + 12) == 0x5a60);

    mg_sdk_audio_prepare_wave_layout(layout, 0x5b00, 34);
    assert(get_u32(layout + 0) == 0x5b00);
    assert(get_u32(layout + 2) == 34);
    return 0;
}
