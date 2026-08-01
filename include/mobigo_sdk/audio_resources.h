#ifndef MOBIGO_SDK_AUDIO_RESOURCES_H
#define MOBIGO_SDK_AUDIO_RESOURCES_H

#include "mobigo_sdk/system_controls.h"

enum {
    MG_SDK_AUDIO_RESOURCE_CLASS_M = 0x004d,
    MG_SDK_AUDIO_RESOURCE_CLASS_W = 0x0057,
    MG_SDK_AUDIO_RESOURCE_CLASS_S = 0x0053,
    MG_SDK_AUDIO_M_HEADER_WORDS = 10,
    MG_SDK_AUDIO_W_RECORD_WORDS = 32,
    MG_SDK_AUDIO_S_HEADER_WORDS = 10,
    MG_SDK_AUDIO_SPF_TAG_WORDS = 4,
    MG_SDK_AUDIO_FIRST_RESOURCE_INDEX = 3,
    MG_SDK_AUDIO_LOCAL_RESOURCE_TAG = 0xc000
};

enum mg_sdk_audio_m_record_word {
    MG_SDK_AUDIO_M_WORD_CLASS = 0,
    MG_SDK_AUDIO_M_WORD_BYTE_LENGTH_LO = 2,
    MG_SDK_AUDIO_M_WORD_BYTE_LENGTH_HI = 3,
    MG_SDK_AUDIO_M_WORD_VERSION = 4,
    MG_SDK_AUDIO_M_WORD_RELOCATION_STATE = 5,
    MG_SDK_AUDIO_M_WORD_STREAM = 10
};

enum mg_sdk_audio_m_event_class {
    MG_SDK_AUDIO_M_EVENT_NOTE = 0x0000,
    MG_SDK_AUDIO_M_EVENT_WAIT = 0x1000,
    MG_SDK_AUDIO_M_EVENT_SKIP_WORD = 0x2000,
    MG_SDK_AUDIO_M_EVENT_CONTROL_CHANGE = 0x3000,
    MG_SDK_AUDIO_M_EVENT_PROGRAM_CHANGE = 0x4000,
    MG_SDK_AUDIO_M_EVENT_MARKER = 0x5000,
    MG_SDK_AUDIO_M_EVENT_END = 0x6000,
    MG_SDK_AUDIO_M_EVENT_AUX_BLOCK_CONTROL = 0x7000,
    MG_SDK_AUDIO_M_EVENT_AUX_BLOCK = 0x8000
};

struct mg_sdk_audio_m_stream_writer {
    mg_sdk_u16 *word;
    mg_sdk_u16 capacity;
    mg_sdk_u16 count;
};

enum mg_sdk_audio_w_record_word {
    MG_SDK_AUDIO_W_WORD_CLASS = 0,
    MG_SDK_AUDIO_W_WORD_BYTE_LENGTH_LO = 2,
    MG_SDK_AUDIO_W_WORD_BYTE_LENGTH_HI = 3,
    MG_SDK_AUDIO_W_WORD_VERSION = 4,
    MG_SDK_AUDIO_W_WORD_RELOCATION_STATE = 5,
    MG_SDK_AUDIO_W_WORD_SPF_TAG = 10,
    MG_SDK_AUDIO_W_WORD_SAMPLE_RATE_LO = 18,
    MG_SDK_AUDIO_W_WORD_SAMPLE_RATE_HI = 19,
    MG_SDK_AUDIO_W_WORD_SAMPLE_COUNT_LO = 20,
    MG_SDK_AUDIO_W_WORD_SAMPLE_COUNT_HI = 21,
    MG_SDK_AUDIO_W_WORD_FORMAT_FLAGS = 26,
    MG_SDK_AUDIO_W_WORD_CONTROL_27 = 27,
    MG_SDK_AUDIO_W_WORD_CONTROL_28 = 28,
    MG_SDK_AUDIO_W_WORD_CONTROL_29 = 29,
    MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_LO = 30,
    MG_SDK_AUDIO_W_WORD_DATA_BYTE_OFFSET_HI = 31
};

/*
 * Resident W-format selection bits recovered from audio_voice_setup_core.
 * Format zero programs the SPU as unsigned 8-bit PCM and is runtime-verified
 * by make audio-check. The other selector combinations are documented by the
 * resident branch/hardware path but are not yet exposed as authoring helpers.
 */
enum mg_sdk_audio_w_format_flags {
    MG_SDK_AUDIO_W_FORMAT_PCM8 = 0x0000,
    MG_SDK_AUDIO_W_FORMAT_PCM16_SELECTOR = 0x0010,
    MG_SDK_AUDIO_W_FORMAT_COMPRESSED_SELECTOR = 0x0040,
    MG_SDK_AUDIO_W_FORMAT_ADPCM36 = 0x00c0,
    MG_SDK_AUDIO_W_FORMAT_ADPCM36_SELECTOR =
        MG_SDK_AUDIO_W_FORMAT_ADPCM36
};

enum {
    MG_SDK_ADPCM36_SAMPLES_PER_FRAME = 32,
    MG_SDK_ADPCM36_DATA_WORDS = 8,
    MG_SDK_ADPCM36_FRAME_WORDS = 9,
    MG_SDK_ADPCM36_END_WORDS = 2
};

struct mg_sdk_audio_w_record {
    mg_sdk_u16 word[MG_SDK_AUDIO_W_RECORD_WORDS];
};

enum {
    MG_SDK_AUDIO_PATCH_ZONE_WORDS = 34,
    MG_SDK_AUDIO_PATCH_GROUP_PREFIX_WORDS = 4,
    MG_SDK_AUDIO_PATCH_GROUP_OFFSET_WORDS = 2,
    MG_SDK_AUDIO_PATCH_GROUP_HEADER_WORDS = 6,
    MG_SDK_AUDIO_PATCH_SINGLE_PROGRAM_GROUP_OFFSET = 20,
    MG_SDK_AUDIO_PATCH_SINGLE_PROGRAM_WORDS = 60,
    MG_SDK_AUDIO_PATCH_ADDRESS_BIAS_WORDS = 0x14
};

enum mg_sdk_audio_patch_zone_word {
    MG_SDK_AUDIO_PATCH_WORD_ROOT_AND_UPPER_KEY = 0,
    MG_SDK_AUDIO_PATCH_WORD_KEY_RANGE =
        MG_SDK_AUDIO_PATCH_WORD_ROOT_AND_UPPER_KEY,
    MG_SDK_AUDIO_PATCH_WORD_CONTROL = 2,
    MG_SDK_AUDIO_PATCH_WORD_ENVELOPE_BYTE_OFFSET = 4,
    MG_SDK_AUDIO_PATCH_WORD_LEVEL_PAIR = 6,
    MG_SDK_AUDIO_PATCH_WORD_RESERVED_10 = 8,
    MG_SDK_AUDIO_PATCH_WORD_RESERVED_14 = 10,
    MG_SDK_AUDIO_PATCH_WORD_SPF_TAG = 12,
    MG_SDK_AUDIO_PATCH_WORD_SIGNATURE_A = 16,
    MG_SDK_AUDIO_PATCH_WORD_SIGNATURE_B = 18,
    MG_SDK_AUDIO_PATCH_WORD_SAMPLE_RATE = 20,
    MG_SDK_AUDIO_PATCH_WORD_RESERVED_2C = 22,
    MG_SDK_AUDIO_PATCH_WORD_LOOP_BIASED_WORD_OFFSET = 24,
    MG_SDK_AUDIO_PATCH_WORD_RESERVED_34 = 26,
    MG_SDK_AUDIO_PATCH_WORD_FORMAT_AND_KEY_COPY = 28,
    MG_SDK_AUDIO_PATCH_WORD_TRAILING_CONTROL = 30,
    MG_SDK_AUDIO_PATCH_WORD_SAMPLE_BYTE_OFFSET = 32
};

/*
 * Low-byte codec selectors consumed by the resident music-zone loader.
 * Retail compressed zones use 0xd4/0xd5; bits 0x04/0x05 are additional
 * title controls, while the codec decision itself is the 0xd0 bit pattern.
 */
enum mg_sdk_audio_patch_format {
    MG_SDK_AUDIO_PATCH_FORMAT_PCM8 = 0x00,
    MG_SDK_AUDIO_PATCH_FORMAT_PCM16 = 0x10,
    MG_SDK_AUDIO_PATCH_FORMAT_COMPRESSED_2 = 0x40,
    MG_SDK_AUDIO_PATCH_FORMAT_COMPRESSED_3 = 0x50,
    MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36_4 = 0xc0,
    MG_SDK_AUDIO_PATCH_FORMAT_ADPCM36 = 0xd0
};

struct mg_sdk_audio_patch_zone {
    mg_sdk_u16 word[MG_SDK_AUDIO_PATCH_ZONE_WORDS];
};

/*
 * A melodic zone is selected by the first zone whose upper_key is greater
 * than or equal to the incoming MIDI note. root_key is the tuning origin used
 * by the resident pitch table; it is not a lower-bound test.
 *
 * sample_byte_offset, loop_word_offset, and envelope_word_offset are all
 * relative to the waveform base in the second root's layout object.
 */
struct mg_sdk_audio_pcm8_zone_spec {
    mg_sdk_u16 root_key;
    mg_sdk_u16 upper_key;
    mg_sdk_u32 sample_rate;
    mg_sdk_u32 sample_byte_offset;
    mg_sdk_u32 loop_word_offset;
    mg_sdk_u32 envelope_word_offset;
};

struct mg_sdk_audio_pcm8_program_spec {
    mg_sdk_u16 program;
    const struct mg_sdk_audio_pcm8_zone_spec *zone;
    mg_sdk_u16 zone_count;
};

/*
 * Channel 9 indexes the percussion directory directly by MIDI note. The
 * resident takes the first zone in that note's group and programs its sample
 * rate without melodic root-key transposition.
 */
struct mg_sdk_audio_pcm8_percussion_spec {
    mg_sdk_u16 note;
    mg_sdk_u32 sample_rate;
    mg_sdk_u32 sample_byte_offset;
    mg_sdk_u32 loop_word_offset;
    mg_sdk_u32 envelope_word_offset;
};

struct mg_sdk_audio_pcm8_patch_bank_spec {
    const struct mg_sdk_audio_pcm8_program_spec *program;
    mg_sdk_u16 program_count;
    const struct mg_sdk_audio_pcm8_percussion_spec *percussion;
    mg_sdk_u16 percussion_count;
};

/* Size/build the complete melodic + direct-note percussion second root. */
mg_sdk_u16 mg_sdk_audio_pcm8_bank_words(
    const struct mg_sdk_audio_pcm8_patch_bank_spec *bank);
mg_sdk_u16 mg_sdk_audio_build_pcm8_bank(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 capacity_words,
    mg_sdk_u32 layout_address,
    const struct mg_sdk_audio_pcm8_patch_bank_spec *bank);

/*
 * Parse an already-built second root and change one zone's low-byte codec
 * selector. These helpers preserve the duplicated root/upper-key bytes and
 * all other zone controls. They return one on success and zero if the named
 * program/note or zone index is absent.
 */
int mg_sdk_audio_patch_prog_fmt(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 program,
    mg_sdk_u16 zone_index,
    mg_sdk_u16 format_byte);
int mg_sdk_audio_patch_drum_fmt(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 note,
    mg_sdk_u16 format_byte);

#define mg_sdk_audio_set_program_zone_format mg_sdk_audio_patch_prog_fmt
#define mg_sdk_audio_set_percussion_format mg_sdk_audio_patch_drum_fmt

/*
 * Return the required melodic-only second-root size, or zero for an invalid
 * program/zone description. Programs must be unique. Zones within each
 * program must have strictly increasing upper_key values.
 */
mg_sdk_u16 mg_sdk_audio_pcm8_root_words(
    const struct mg_sdk_audio_pcm8_program_spec *programs,
    mg_sdk_u16 program_count);

/*
 * Build a capacity-checked melodic PCM8 patch root. Returns words written, or
 * zero when the description/capacity is invalid. The percussion directory is
 * emitted empty; multiple melodic programs and multiple key zones are
 * supported.
 */
mg_sdk_u16 mg_sdk_audio_build_pcm8_root(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 capacity_words,
    mg_sdk_u32 layout_address,
    const struct mg_sdk_audio_pcm8_program_spec *programs,
    mg_sdk_u16 program_count);

/*
 * Build the compact second audio root used by a single melodic PCM8 program.
 * `patch_root` must provide 60 words. The primary directory maps `program` to
 * one one-zone group; the percussion directory is empty.
 *
 * sample_byte_offset is relative to the patch waveform base supplied by the
 * second-root layout object. Loop/envelope offsets are word offsets from that
 * same waveform base; this helper applies the resident's internal +0x14 bias.
 */
void mg_sdk_audio_pcm8_single_root(
    mg_sdk_u16 *patch_root,
    mg_sdk_u32 layout_address,
    mg_sdk_u16 program,
    mg_sdk_u16 root_key,
    mg_sdk_u16 upper_key,
    mg_sdk_u32 sample_rate,
    mg_sdk_u32 sample_byte_offset,
    mg_sdk_u32 loop_word_offset,
    mg_sdk_u32 envelope_word_offset);

/*
 * Source-compatible long names. The Generalplus assembler truncates external
 * symbols, so the actual emitted function names above intentionally stay at
 * 30 characters or fewer.
 */
#define mg_sdk_audio_pcm8_patch_bank_words mg_sdk_audio_pcm8_bank_words
#define mg_sdk_audio_prepare_pcm8_patch_bank mg_sdk_audio_build_pcm8_bank
#define mg_sdk_audio_pcm8_patch_root_words mg_sdk_audio_pcm8_root_words
#define mg_sdk_audio_prepare_pcm8_patch_root mg_sdk_audio_build_pcm8_root
#define mg_sdk_audio_prepare_single_pcm8_patch_root \
    mg_sdk_audio_pcm8_single_root

/* Two-word envelope segment used by the runtime-verified clean PCM8 patch. */
void mg_sdk_audio_prepare_hold_envelope(
    mg_sdk_u16 *envelope_words,
    mg_sdk_u16 hold_ticks);

/* Prepare the 10-word M header for an already-authored event stream. */
void mg_sdk_audio_prepare_m_header(
    mg_sdk_u16 *record_words,
    mg_sdk_u16 payload_word_count);

void mg_sdk_audio_m_writer_init(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 *stream_words,
    mg_sdk_u16 capacity_words);
/*
 * 0x5xxx stores its low byte in sequencer metadata. Retail values are
 * BPM-shaped, but no recovered resident reader uses that field for beat
 * timing, so keep the API neutral until another consumer proves its meaning.
 */
int mg_sdk_audio_m_write_marker(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 value);
int mg_sdk_audio_m_write_program_change(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 channel,
    mg_sdk_u16 program);
int mg_sdk_audio_m_write_control_change(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 channel,
    mg_sdk_u16 controller,
    mg_sdk_u16 value);
/* 0x2xxx consumes and discards one following stream word. */
int mg_sdk_audio_m_write_skip_word(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 skipped_word);
/*
 * Copy an inline block into resident music scratch buffer 0x0397. The low
 * event byte is the word count. Class 7 first consumes one control word and
 * may invoke an optional title callback with channel/count/scratch address;
 * class 8 performs only the block transfer. Both commands continue parsing
 * at the word immediately following the block.
 *
 * These classes are absent from the inspected retail M songs. Keep blocks
 * small: the recovered resident destination is a fixed low-RAM scratch area.
 */
int mg_sdk_audio_m_write_aux_cb(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 channel,
    mg_sdk_u16 control_word,
    const mg_sdk_u16 *block_words,
    mg_sdk_u16 block_word_count);
int mg_sdk_audio_m_write_aux(
    struct mg_sdk_audio_m_stream_writer *writer,
    const mg_sdk_u16 *block_words,
    mg_sdk_u16 block_word_count);
int mg_sdk_audio_m_write_note(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 channel,
    mg_sdk_u16 note,
    mg_sdk_u16 velocity,
    mg_sdk_u16 duration);
int mg_sdk_audio_m_write_wait(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 ticks);
int mg_sdk_audio_m_write_end(
    struct mg_sdk_audio_m_stream_writer *writer);

/*
 * S resources are variable-length sequence wrappers. They have a 10-word
 * header followed by 32-bit child-resource references and a final
 * 0xffffffff terminator. The resident keeps the current child index in the
 * active voice and advances automatically when each child finishes.
 */
enum mg_sdk_audio_s_record_word {
    MG_SDK_AUDIO_S_WORD_CLASS = 0,
    MG_SDK_AUDIO_S_WORD_BYTE_LENGTH_LO = 2,
    MG_SDK_AUDIO_S_WORD_BYTE_LENGTH_HI = 3,
    MG_SDK_AUDIO_S_WORD_VERSION = 4,
    MG_SDK_AUDIO_S_WORD_RELOCATION_STATE = 5,
    MG_SDK_AUDIO_S_WORD_SEQUENCE_OFFSET_LO = 8,
    MG_SDK_AUDIO_S_WORD_SEQUENCE_OFFSET_HI = 9,
    MG_SDK_AUDIO_S_WORD_SEQUENCE = 10
};

/*
 * Build the resident-compatible 32-word W record for unsigned 8-bit PCM.
 * byte_length includes the 0xffff SPU terminator/padding stored in the sample
 * payload. data_byte_offset is relative to the audio base supplied through
 * the registrar's terminal layout object.
 */
void mg_sdk_audio_prepare_w_pcm8(
    struct mg_sdk_audio_w_record *record,
    mg_sdk_u32 byte_length,
    mg_sdk_u32 sample_rate,
    mg_sdk_u32 sample_count,
    mg_sdk_u32 data_byte_offset);

/*
 * Build a format-6 W record for the SPU ADPCM36 path. The sample payload is a
 * sequence of nine-word frames (header + eight packed-nibble words), followed
 * by the two words emitted by mg_sdk_adpcm36_finish().
 */
void mg_sdk_audio_w_adpcm36(
    struct mg_sdk_audio_w_record *record,
    mg_sdk_u32 byte_length,
    mg_sdk_u32 sample_rate,
    mg_sdk_u32 sample_count,
    mg_sdk_u32 data_byte_offset);

/*
 * Encode one independent predictor-zero ADPCM36 frame. This clean-room mode
 * chooses the finest shift that contains the input range, packs samples in
 * low-nibble-first order, and does not depend on previous frames.
 */
mg_sdk_u16 mg_sdk_adpcm36_encode_frame(
    mg_sdk_u16 *output_words,
    const mg_sdk_s16 *samples);

/* Append the dummy header + 0xffff data sentinel required by the SPU reader. */
void mg_sdk_adpcm36_finish(mg_sdk_u16 *output_words);

#define mg_sdk_audio_prepare_w_adpcm36 mg_sdk_audio_w_adpcm36

/*
 * Build an inline S sequence from local resource-table IDs. `record_words`
 * must provide at least 10 + 2*(child_count + 1) words. Child IDs are encoded
 * with the 0xc000 local-resource tag used by every S entry in the G1 corpus.
 */
void mg_sdk_audio_prepare_s_sequence(
    mg_sdk_u16 *record_words,
    const mg_sdk_u16 *child_resource_ids,
    mg_sdk_u16 child_count);

/*
 * Prepare a complete title audio-resource root. Resource addresses must be
 * ordered M entries first, then W, then S. `root` requires
 * 6 + 2*(m_count + w_count + s_count) + 2 words.
 */
void mg_sdk_audio_prepare_root(
    mg_sdk_u16 *root,
    mg_sdk_u16 m_count,
    mg_sdk_u16 w_count,
    mg_sdk_u16 s_count,
    const mg_sdk_u32 *resource_addresses,
    mg_sdk_u32 layout_address);

/*
 * Prepare the compact single-W root used by the clean-room homebrew path.
 * root must provide at least 10 words. Resource ID 3 resolves to w_record.
 */
void mg_sdk_audio_prepare_single_w_root(
    mg_sdk_u16 *root,
    mg_sdk_u32 w_record_address,
    mg_sdk_u32 layout_address);

/*
 * Prepare the first terminal layout pair: waveform base (word address) and
 * region length (words). layout must provide at least four words.
 */
void mg_sdk_audio_prepare_wave_layout(
    mg_sdk_u16 *layout,
    mg_sdk_u32 wave_base_word_address,
    mg_sdk_u32 wave_region_words);

/*
 * Build the 14-word zero-program/zero-percussion second root. This is enough
 * to initialize the resident sequencer for M streams that do not play notes,
 * such as timing, marker, skip, or auxiliary-block command tests.
 */
void mg_sdk_audio_prepare_empty_patch_root(
    mg_sdk_u16 *patch_root,
    mg_sdk_u32 layout_address);

#endif
