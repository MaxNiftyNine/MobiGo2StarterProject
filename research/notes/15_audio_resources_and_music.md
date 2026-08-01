# Audio resources and resident music sequencer

This note is the authoritative audio-format handoff. Names are clean-room
working names, not claimed retail symbols.

## Registration boundary

Resident service `0x075e06` registers two roots:

1. a title root containing M, W, and S resources;
2. a patch/instrument root used by the M note engine.

W and S effects work with a null second root. M initialization requires a valid
second root, even if both patch directories are empty. Registration builds
128-entry melodic and percussion maps, initializes 16 channel states, programs
the SPU beat timer, and installs callback `0x062de2`.

```c
mg_sdk_resident_register_audio_resources(title_root, patch_root);
```

## Resident services

| Service | Target | Meaning |
|---:|---:|---|
| `0x075e06` | `0x05ef19` | register title resources / optional patch root |
| `0x075e0e` | `0x05f3f8` | play W or S sound |
| `0x075e1a` | `0x05f90f` | query sound state |
| `0x075e2c` | `0x05fb41` | play M music |
| `0x075e32` | `0x05fd4a` | pause music |
| `0x075e34` | `0x05fd61` | resume music |
| `0x075e36` | `0x05fd78` | stop music |
| `0x075e38` | `0x05fde0` | query music state |
| `0x075e3c` | `0x05fe1b` | set repeat |
| `0x075e3e` | `0x05fe38` | get level |
| `0x075e40` | `0x05fe53` | set level |

Observed music states are 0 stopped, 1 paused, 2 playing, and 4 a released
stopped variant. Handles contain a slot and generation; consecutive use of the
same slot produced `0x40000004`, `0x40010004`, and later generations.

## Title root

```text
u32 m_count
u32 w_count
u32 s_count
u32 resource[m_count + w_count + s_count]
u32 terminal_layout
```

Resources are ordered M, then W, then S. Local IDs begin at 3. The terminal
waveform layout used by clean resources is:

```text
u32 waveform_base_word_address
u32 waveform_region_words
```

Helpers: `mg_sdk_audio_prepare_root()`,
`mg_sdk_audio_prepare_single_w_root()`, and
`mg_sdk_audio_prepare_wave_layout()`.

## W: single waveform

W is 32 words. Important fields:

| Word | Meaning |
|---:|---|
| 0 | `'W'` (`0x0057`) |
| 2..3 | byte length |
| 4 | version 2 |
| 5 | relocation state |
| 10..13 | packed `SPF2ALP\0` |
| 18..19 | sample rate |
| 20..21 | sample count |
| 26 | format flags |
| 27..29 | mixer/control defaults |
| 30..31 | byte offset from waveform base, relocated to byte address |

Format selection recovered from `0x06234b`:

- `0x00`: unsigned PCM8;
- `0x10`: PCM16;
- `0x40`: compressed format 2;
- `0x50`: compressed format 3;
- `0xc0`: format 6, ADPCM36.

`make audio-check` proves const PCM8 relocation, handle `0x40000000`, and
4 kHz pitch `0x1d1d`. `make adpcm-check` proves generated format-6 ADPCM36,
SPU mode `0x938e`, channel format register `0xbe00`, 1 kHz pitch `0x0747`,
and natural completion.

## S: ordered effect sequence

S is a 10-word header followed by 32-bit child resource references and a final
`0xffffffff`. Local references use `0xc000 | resource_id`.

The active voice retains its child index. On W completion the resident loads the
next child into the same voice. At the sentinel, repeat zero stops and repeat
nonzero returns to child zero. This proves the fifth sound-play argument is
repeat/loop. The clean two-child proof transitions 4 kHz to 6 kHz at the exact
second waveform address.

## M: compact MIDI-derived stream

M has a 10-word header and a 16-bit command stream. The complete dispatcher is:

| Class | Stream behavior |
|---:|---|
| `0x0ccc` | note; channel is low nibble, then `(note<<8)|velocity`, then duration |
| `0x1xxx` | wait; low 11 bits, with optional three high bits in a second word |
| `0x2xxx` | consume/discard one following word |
| `0x3cNN` | Control Change, then one value word |
| `0x4cPP` | Program Change |
| `0x50VV` | store opaque low-byte metadata marker |
| `0x6xxx` | end; stop or rewind according to repeat |
| `0x7cNN` | consume one control word, copy NN inline words to `0x0397`, optionally call title callback for channel c |
| `0x80NN` | copy NN inline words to `0x0397` without callback |

Public writers cover every class. The inspected G1/G2/SY songs contain 5,456
notes and 1,859 waits and parse to their end markers. Those retail streams do
not use 2/3/7/8, but resident code supports them. `make music-aux-check`
independently proves 2/7/8 stream synchronization and final scratch words
`0x9abc/0xdef0` under automatic beat IRQ timing.

The Control Change handler recognizes MIDI controllers 7 Volume, 10 Pan,
11 Expression, 32 Bank LSB, 38 Data Entry LSB, 100/101 RPN LSB/MSB, and
6 Data Entry MSB.

Retail `0x5xxx` values look BPM-like, but no recovered reader uses the stored
byte to program beat timing. The API therefore calls it a marker, not tempo.

## Patch root

The second root is:

```text
prefix[10]              // words 2..3 point to waveform layout
u32 melodic_count
entry melodic[]
u32 percussion_count
entry percussion[]
packed groups...
```

Each six-word entry is `{u32 id, u32 group_byte_offset,
u32 group_byte_length}`. Melodic IDs are program numbers; percussion IDs are
MIDI notes.

A group is:

```text
u32 zone_count
u32 zone_table_byte_offset
u32 zone_relative_byte_offset[zone_count]
zone[zone_count]        // 34 words each
```

For the complete clean bank:

```text
14 + 10*program_count + 36*melodic_zone_count
   + 46*percussion_count                         words
```

`mg_sdk_audio_build_pcm8_bank()` validates IDs, capacities, MIDI ranges, and
strictly increasing upper-key thresholds. `mg_sdk_audio_prepare_empty_patch_root()`
initializes M streams that do not need notes.

## Zone grammar used by clean authoring

| Word | Meaning |
|---:|---|
| 0 | root key in low byte, upper-key threshold in next byte |
| 2..3 | common control `0x64400602` |
| 4..5 | envelope byte offset with internal +0x14-word bias |
| 6..7 | level pair `0x7f7f` |
| 12..15 | `SPF2ALP\0` |
| 16..19 | invariant signatures |
| 20..21 | base sample rate |
| 24..25 | loop word offset with internal +0x14 bias |
| 28..29 | duplicated keys and low-byte codec selector |
| 30..31 | trailing control `0x00000602` |
| 32..33 | sample byte offset |

The resident chooses the first melodic zone whose upper-key threshold is at
least the incoming note. Root key drives transposition. Channel 9 indexes the
percussion directory directly and does not apply melodic root transposition.

Zone codec bytes recovered from `0x061d18` include `0x00` PCM8 and `0xd0`
ADPCM36 internal format 5. Retail `0xd4/0xd5` values add low control bits; the
codec selection itself is `0xd0`. Parser-backed setters alter only the codec
byte of a selected program zone or percussion entry.

## ADPCM36 stream and encoder

A frame is one header word plus eight words of low-nibble-first data, producing
32 samples. The header low nibble is a right shift; bits 4..9 are a signed
first-order predictor coefficient. The decoder computes:

```text
sample = (signed_nibble << 12 >> shift)
       + ((previous * coefficient + 32) >> 12)
```

A finite stream ends with a dummy header followed by `0xffff`, because the SPU
fetches the next frame header before testing the first data word for the end
marker.

The target helper `mg_sdk_adpcm36_encode_frame()` emits independent
predictor-zero frames. `tools/assets/build_adpcm36_audio.py` is the practical offline
encoder: it accepts PCM WAV, optionally downmixes, searches all 64 signed
coefficients and 13 shifts per frame, simulates the recovered decoder, and emits
C/header, raw stream, JSON metrics, and decoded WAV preview. It can append a
hold envelope outside the stream length for M zones.

The MBA builder accepts repeatable `--extra-source` arguments so generated
assets compile as ordinary translation units with their directories added to
the include path.

## Automatic beat scheduling

The resident initializer `0x06286a` programs:

- `0x7b84`: 11-bit beat base;
- `0x7b85`: 14-bit count plus enable/status bits;
- Status3 bit 2 at `0x78a3`;
- optional FIQ route through Priority3 bit 2 at `0x78a6`.

Normal SPU routing is IRQ4. Generalplus driver evidence establishes one base
unit as four 281.25 kHz service frames. A count field of zero is the minimum
one-base heartbeat, not disabled; the resident intentionally leaves `0x8000`
programmed while idle so newly started music is noticed.

The emulator directly models the timer, IRQ4/FIQ route, W1C status, stop
command, channel-active state, natural completion, and descriptor rewrite
synchronization in `emulator/src/audio.hpp` and `emulator/src/bus.hpp`.
`tools/build/emulator_macos.sh --test` builds it and runs CTest.

No homebrew example calls `0x062de2` directly anymore.

## Runtime proofs

`make music-check` verifies four sequential M songs:

| Selection | Wave | Rate | Pitch | Pan/velocity |
|---|---:|---:|---:|---:|
| program 0 note 60 | base | 4000 | `0x1d1d` | `0x405a` |
| program 0 note 72 | base+34 | 6000 | `0x2bab` | `0x4064` |
| program 7 note 60 | base+68 | 8000 | `0x3a3a` | `0x406e` |
| percussion 36 | base+102 | 5000 | `0x2464` | `0x4078` |

All four use automatic IRQ4 and stop at application frames 16/31/47/62.

`make music-adpcm-check` converts a WAV, links the generated C, selects zone
codec `0xd0`, and verifies resident music handle `0x40000004`, SPU mode
`0xf38e`, format register `0xbe00`, pitch `0x0747`, velocity/pan `0x4064`, and
state `2 -> 0` at frame 17.

## Evidence boundary

The common effect/music authoring path is complete enough for homebrew. Still
not named completely are advanced envelope and rare control fields for which no
independent consumer exists. A 2026-08-01 physical-console run confirmed
audible generated PCM/S/ADPCM and M playback. It also established that return
registers from the state/control services are not portable success booleans;
callers must validate handles and the state/level values written through output
pointers. Emulator decoder/setup/transport behavior remains covered by the
repeatable regressions.
