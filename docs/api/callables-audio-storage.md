# Audio and storage callables

## `audio.h` — portable state interpretation

```c
int mg_sdk_sound_state_is_playing(mg_sdk_u16 resident_state);
```

Returns one for `MG_SDK_SOUND_STATE_PLAYING`, zero for a known non-playing
state, and `-1` for an unknown/error state. It is host-testable and avoids
treating a raw resident call's return register as a portable boolean.

## `audio_resources.h` — PCM8 patch banks and roots

```c
mg_sdk_u16 mg_sdk_audio_pcm8_bank_words(
    const struct mg_sdk_audio_pcm8_patch_bank_spec *bank);

mg_sdk_u16 mg_sdk_audio_build_pcm8_bank(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 capacity_words,
    mg_sdk_u32 layout_address,
    const struct mg_sdk_audio_pcm8_patch_bank_spec *bank);

int mg_sdk_audio_patch_prog_fmt(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 program,
    mg_sdk_u16 zone_index,
    mg_sdk_u16 format_byte);

int mg_sdk_audio_patch_drum_fmt(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 note,
    mg_sdk_u16 format_byte);

mg_sdk_u16 mg_sdk_audio_pcm8_root_words(
    const struct mg_sdk_audio_pcm8_program_spec *programs,
    mg_sdk_u16 program_count);

mg_sdk_u16 mg_sdk_audio_build_pcm8_root(
    mg_sdk_u16 *patch_root,
    mg_sdk_u16 capacity_words,
    mg_sdk_u32 layout_address,
    const struct mg_sdk_audio_pcm8_program_spec *programs,
    mg_sdk_u16 program_count);

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

void mg_sdk_audio_prepare_hold_envelope(
    mg_sdk_u16 *envelope_words,
    mg_sdk_u16 hold_ticks);
```

The `*_words()` calls validate descriptions and return required word capacity,
or zero. The `*_build_*()` calls return words written, or zero for invalid
specification/capacity. A bank supports multiple melodic programs/zones and
direct-note percussion; a root is melodic-only. Program IDs must be unique and
zone upper keys strictly increasing.

`mg_sdk_audio_patch_prog_fmt()` and `mg_sdk_audio_patch_drum_fmt()` modify one
already-built zone's low-byte codec selector, returning one when found and zero
when absent/invalid. The single-root helper writes the compact 60-word,
one-program/one-zone form. The envelope helper writes the two-word hold segment.
All outputs are caller-owned; layout/sample/loop/envelope offsets use the units
stated in the structs, so do not convert every field as though it were a word
address.

Long compatibility names are macros mapping to these shortened external names;
the target assembler's external-symbol limit is why callable names are compact.
Builders are host-tested and their maintained PCM8/ADPCM36 patch roots are
firmware-emulator verified.

## `audio_resources.h` — M stream writer

```c
void mg_sdk_audio_prepare_m_header(
    mg_sdk_u16 *record_words,
    mg_sdk_u16 payload_word_count);

void mg_sdk_audio_m_writer_init(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 *stream_words,
    mg_sdk_u16 capacity_words);

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
int mg_sdk_audio_m_write_skip_word(
    struct mg_sdk_audio_m_stream_writer *writer,
    mg_sdk_u16 skipped_word);
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
```

Prepare writes the ten-word M header for an already-authored payload. Writer
init binds caller-owned stream storage and resets count. Every `mg_sdk_audio_m_write_*`
call returns one after appending its complete event and zero without a partial
multiword event when capacity/input validation fails. Marker uses the low byte;
channels are four bits; note/velocity are seven bits. Wait selects short or
extended encoding automatically.

Aux blocks are limited to 255 words and use a fixed resident scratch area;
`mg_sdk_audio_m_write_aux_cb()` includes channel/control callback metadata while
`mg_sdk_audio_m_write_aux()` only copies the block. These rare classes are
emulator-inferred from resident code and tests; they were absent from the
inspected retail M corpus. Notes/program/control/wait/end and automatic SPU beat
progression have stronger integration evidence.

## `audio_resources.h` — W, ADPCM36, S, and roots

```c
void mg_sdk_audio_prepare_w_pcm8(
    struct mg_sdk_audio_w_record *record,
    mg_sdk_u32 byte_length,
    mg_sdk_u32 sample_rate,
    mg_sdk_u32 sample_count,
    mg_sdk_u32 data_byte_offset);

void mg_sdk_audio_w_adpcm36(
    struct mg_sdk_audio_w_record *record,
    mg_sdk_u32 byte_length,
    mg_sdk_u32 sample_rate,
    mg_sdk_u32 sample_count,
    mg_sdk_u32 data_byte_offset);

mg_sdk_u16 mg_sdk_adpcm36_encode_frame(
    mg_sdk_u16 *output_words,
    const mg_sdk_s16 *samples);

void mg_sdk_adpcm36_finish(mg_sdk_u16 *output_words);

void mg_sdk_audio_prepare_s_sequence(
    mg_sdk_u16 *record_words,
    const mg_sdk_u16 *child_resource_ids,
    mg_sdk_u16 child_count);

void mg_sdk_audio_prepare_root(
    mg_sdk_u16 *root,
    mg_sdk_u16 m_count,
    mg_sdk_u16 w_count,
    mg_sdk_u16 s_count,
    const mg_sdk_u32 *resource_addresses,
    mg_sdk_u32 layout_address);

void mg_sdk_audio_prepare_single_w_root(
    mg_sdk_u16 *root,
    mg_sdk_u32 w_record_address,
    mg_sdk_u32 layout_address);

void mg_sdk_audio_prepare_wave_layout(
    mg_sdk_u16 *layout,
    mg_sdk_u32 wave_base_word_address,
    mg_sdk_u32 wave_region_words);

void mg_sdk_audio_prepare_empty_patch_root(
    mg_sdk_u16 *patch_root,
    mg_sdk_u32 layout_address);
```

The two W builders fill a caller-owned 32-word record for PCM8 or ADPCM36.
Lengths/sample offsets are bytes where named; layout/base values are words.
`mg_sdk_adpcm36_encode_frame()` consumes exactly 32 signed samples, writes one
nine-word predictor-zero frame, and returns the selected shift; it returns
`0xffff` for null input/output. `mg_sdk_adpcm36_finish()` writes the required
two-word terminator immediately after the last frame.

The S builder writes a ten-word header, tagged local child IDs, and a
`0xffffffff` terminator; caller capacity is at least
`10 + 2 * (child_count + 1)` words. The general root orders M, then W, then S
addresses and needs `6 + 2 * total + 2` words. The single-W, four-word wave
layout, and 14-word empty patch helpers are compact special cases. Void builders
ignore null top-level output but cannot validate caller capacity; size first.

PCM8, S, ADPCM36, and maintained M subsets have deterministic emulator and
bounded audible hardware evidence. Unexposed codec combinations remain unknown.

## `resident_audio.h` — target playback

```c
void mg_sdk_resident_register_audio_resources(
    mg_sdk_u16 *title_resource_root,
    mg_sdk_u16 *shared_patch_root);

mg_sdk_u32 mg_sdk_resident_play_sound(
    mg_sdk_u32 resource,
    mg_sdk_u16 gain,
    mg_sdk_u16 pan,
    mg_sdk_u16 repeat,
    mg_sdk_u16 mode);

int mg_sdk_resident_get_sound_state(
    mg_sdk_u32 handle,
    mg_sdk_u16 *state);
int mg_sdk_resident_sound_is_playing(mg_sdk_u32 handle);

mg_sdk_u32 mg_sdk_resident_play_music(
    mg_sdk_u32 resource,
    mg_sdk_u16 level,
    mg_sdk_u16 repeat,
    mg_sdk_u16 mode);
int mg_sdk_resident_pause_music(mg_sdk_u32 handle);
int mg_sdk_resident_resume_music(mg_sdk_u32 handle);
int mg_sdk_resident_stop_music(mg_sdk_u32 handle);
int mg_sdk_resident_get_music_state(
    mg_sdk_u32 handle,
    mg_sdk_u16 *state);
int mg_sdk_resident_set_music_repeat(
    mg_sdk_u32 handle,
    mg_sdk_u16 repeat);
int mg_sdk_resident_get_music_level(
    mg_sdk_u32 handle,
    mg_sdk_u16 *level);
int mg_sdk_resident_set_music_level(
    mg_sdk_u32 handle,
    mg_sdk_u16 level);
```

Registration binds caller-owned mutable title/patch roots for resident use;
keep them and referenced data valid while audio can play. Play calls return
opaque 32-bit handles. A sound resource may be a small table ID or a far
structured pointer. Gain/level, pan, repeat, and allocation mode retain the
resident contract rather than host-audio units.

Getters write the requested state/level. `mg_sdk_resident_sound_is_playing()`
interprets the written state and is the preferred sound boolean. Music states
observed are stopped `0/4`, paused `1`, and playing `2`. Physical evidence shows
that raw return registers from music control/query services are not portable
success booleans: validate handles and observable written state/output instead
of writing `if (pause(...))` logic.

Target-only. Digital state and output are emulator-verified; maintained formats
have bounded audible hardware evidence, while analog quality/edge codecs remain
limited.

## `resident_storage.h` — target files

```c
int mg_sdk_storage_pack_path(
    mg_sdk_u16 *destination,
    const char *source);

mg_sdk_file_handle mg_sdk_resident_file_open(
    const char *path,
    mg_sdk_u16 mode);
int mg_sdk_resident_file_close(mg_sdk_file_handle handle);
mg_sdk_u32 mg_sdk_resident_file_read(
    void *destination,
    mg_sdk_u32 byte_count,
    mg_sdk_file_handle handle);
mg_sdk_u32 mg_sdk_resident_file_write(
    const void *source,
    mg_sdk_u32 byte_count,
    mg_sdk_file_handle handle);
int mg_sdk_resident_file_truncate(mg_sdk_file_handle handle);
int mg_sdk_resident_file_seek_absolute(
    mg_sdk_file_handle handle,
    mg_sdk_u32 byte_offset);
mg_sdk_u32 mg_sdk_resident_file_size(mg_sdk_file_handle handle);
int mg_sdk_resident_storage_path_exists(const char *path);
int mg_sdk_resident_storage_path_remove(const char *path);
```

`mg_sdk_storage_pack_path()` converts an ordinary target C string into the
resident two-characters-per-word form, returning one when it fits the 27-char
limit and zero otherwise. All path-taking wrappers perform this automatically.
Open returns a four-slot/generation handle or `MG_SDK_INVALID_FILE_HANDLE`.
Modes are `MG_SDK_FILE_OPEN_READ`, `WRITE`, or `READ_WRITE`.

Read/write return transferred byte counts or `MG_SDK_FILE_IO_ERROR`. Size
returns bytes or that same sentinel. Seek is an absolute byte offset and rejects
past EOF. Truncate uses current position. Close, truncate, seek, and remove use
the resident integer convention documented in the header; observed successful
truncate/remove return zero. The path predicate returns
`MG_SDK_STORAGE_PATH_MISSING`, `FILE`, or `DIRECTORY`.

Buffers remain caller-owned for each synchronous call. Handles must be closed
and are invalid after close. Existing-file operations have copied-NAND
integration coverage; fresh-path directory publication remains experimental and
physical diagnostics should stay read-only.
