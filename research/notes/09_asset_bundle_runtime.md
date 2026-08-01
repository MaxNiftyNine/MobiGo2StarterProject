# Linked asset bundle and standard UI runtime

This note describes the common asset-container and UI-object layer used by
G1, G2, G3, G4, and SY. It records structure and behavior only. No retail
artwork, audio, or executable data is copied into this project.

Names are clean-room working names, not recovered vendor symbols. Word
offsets are 16-bit u'nSP words, not bytes.

## Result

The repeated volume, brightness, and Off presentation comes from two shared
pieces:

1. common runtime code knows which UI mode to select and how to position,
   update, and time the object;
2. each title links a resource bundle containing the descriptors and
   title-local resource pointers used by those UI objects.

The behavior and descriptor schemas are common. Numeric descriptor indices,
sound IDs, and linked graphic pointers are assigned per application.

## Registration

Resident service `0x075f00` resolves to implementation `0x056820`, which
forwards three far pointers to the bundle registrar:

```c
register_asset_bundle(bundle_header, primary_storage, secondary_storage);
```

G1 calls it during `sdk_runtime_init` with:

```text
bundle header:     0x0e2160
primary storage:   far pointer loaded from G1 data 0x103dd0
secondary storage: 0
```

SY uses bundle header `0x0f30ba` and its own primary-storage pointer. The
registrar reads the first 32-bit header value, selects the normal relocation
path for observed value `0x80000002`, and rebases both top-level and nested
pointers in place.

The registration ABI is **Strong**: its six argument words and behavior are
confirmed in the G1 caller and resident implementation. The meanings of the
two optional storage bases are still working names.

## Header

The header occupies `0x20` words. Before relocation, table pointers are word
offsets relative to:

```text
bundle_header + 0x20 words
```

The recovered fields are:

| Word | Width | Meaning | Confidence |
|---:|---:|---|---|
| `0x00` | 2 | relocation/version state; observed `0x80000002` | Strong |
| `0x02` | 2 | primary-relative 512-entry RGB555 palette source for hardware `0x000..0x0ff` and `0x200..0x2ff` | Verified |
| `0x04` | 2 | primary-relative 512-entry RGB555 palette source for hardware `0x100..0x1ff` and `0x300..0x3ff` | Verified |
| `0x06` | 2 | secondary-storage window pointer 0 | Strong structure |
| `0x08` | 2 | secondary-storage window pointer 1 | Strong structure |
| `0x0a` | 1 | large lookup-family count | Strong |
| `0x0b` | 1 | unresolved | Unknown |
| `0x0c` | 2 | large lookup-family table | Strong |
| `0x0e` | 2 | unresolved | Unknown |
| `0x10` | 2 | auxiliary table pointer | Strong structure, unknown role |
| `0x12` | 1 | UI family-A descriptor count | Strong |
| `0x13` | 1 | unresolved | Unknown |
| `0x14` | 2 | UI family-A descriptor table | Strong |
| `0x16` | 1 | UI family-B descriptor count | Strong |
| `0x17` | 1 | unresolved | Unknown |
| `0x18` | 2 | UI family-B descriptor table | Strong |
| `0x1a` | 2 | generated-handle/auxiliary pointer table | Strong structure |
| `0x1c` | 4 | unresolved | Unknown |

Observed counts:

| Bundle | Lookup | Family A | Family B |
|---|---:|---:|---:|
| G1 | `0x0713` | `0x0008` | `0x0032` |
| SY | `0x02d5` | `0x000c` | `0x001d` |

Resident descriptor loaders prove that family-A records are 10 words and
family-B records are 12 words. Their implementation addresses in the captured
resident runtime are `0x066d61` and `0x066e1e`.

The large lookup family is a four-word chunk directory, not a table of
32-bit pointers:

```text
u16 packed_dimensions; /* width in low byte, height in high byte */
u16 flags;
u32 pixel_data_pointer;
```

Every chunk referenced by the standard settings bitmap graph also occurs in
this directory. Directory indices are link-generated and vary widely between
titles; consumers must follow the chunk pointer rather than treating an index
as a stable SDK resource ID.

## Pointer classes

The top two bits of a stored 32-bit pointer select its relocation base:

| Top bits | Stored class | Relocation |
|---:|---|---|
| `00` | bundle-relative | add `bundle_header + 0x20` where the graph walker expects a linked-bundle pointer |
| `10` | primary-storage-relative | clear bit 31 and add the primary storage base passed to `0x075f00` |
| `11` | secondary-storage-relative | clear bits 31..30 and add the secondary storage base |
| `01` | unresolved/banked class | do not emit yet |

This is directly visible in the resident relocation arithmetic. G1 header
values `0x8001c5e0` and `0x8001c7e0` use the primary class; both G1 and SY
also contain secondary-class values `0xc0000000` and `0xc0000100`. Since
their registration calls pass a null secondary base, the resident path
disables the associated secondary windows.

The clean-room API provides tag helpers for primary- and
secondary-storage-relative word offsets. These tags apply to the packed
resource representation; they are not directly dereferenceable C pointers.

The observed version-2 header (`0x80000002`) follows registrar path `0x065fb2`
into full palette loader `0x065ec8`. That loader copies both 256-entry halves
of each 512-entry source through palette copier `0x064a34`:

| Header source | Source entries | Hardware entries |
|---|---:|---:|
| words `2..3` | `0x000..0x0ff` | `0x000..0x0ff` |
| words `2..3` | `0x100..0x1ff` | `0x200..0x2ff` |
| words `4..5` | `0x000..0x0ff` | `0x100..0x1ff` |
| words `4..5` | `0x100..0x1ff` | `0x300..0x3ff` |

Helper `0x06ae9c` is instead part of the older version-1 special path and
must not be used to describe version-2 bundle registration. The PPU setup at
`0x063665` initializes palette-control bit 0, so sprites add `0x100` to the
attribute-selected palette offset. Palette entries are RGB555; bit 15 marks a
transparent entry in the renderer.

## UI service families

| Service | Working role |
|---:|---|
| `0x075f06` | create family-A object |
| `0x075f08` | destroy family-A object |
| `0x075f0e` | get family-A mutable storage |
| `0x075f12` | create family-B object |
| `0x075f14` | destroy family-B object |
| `0x075f18` | get family-B mutable storage |
| `0x075f1c` | bind an object callback/control record |

The public constructors take one 32-bit descriptor ID. All verified
application callers use a zero high word and put the descriptor index in the
low word, for example G1's `0x0000000e`. The normal service path supplies
bundle-registration slot zero internally. In the lower descriptor loader,
slot zero uses the primary registered header and the high bit of the 16-bit
index selects the secondary registered header. The meaning of nonzero
constructor high words remains unresolved and is not exposed as a “bundle
slot” in the clean-room API.

Family-B creation expands a 12-word linked descriptor into runtime object
storage. Descriptor words `0..5` copy to object words `0..5`; object words
`6..7` are cleared; descriptor words `6..11` populate the later object
fields, preserving both far pointers. The constructor then initializes more
runtime state. This explains why callers modify the returned storage instead
of directly editing linked descriptors.

## Standard settings object

G1 creates family-B descriptor `0x0e` for the settings overlay and descriptor
`0x30` for power-off presentation. SY uses `0x01` and `0x17` respectively.

All four descriptors have the same 12-word template:

```text
0001 0000 0000 0000 0000 0000
0000 0040 ffff ffff <nested pointer low> <nested pointer high>
```

Only the final linked pointer differs. This is direct evidence of a common
SDK object descriptor template with per-title linked resources.

| Object | G1 raw nested pointer | SY raw nested pointer |
|---|---:|---:|
| settings | `0x00010ac6` | `0x000018a8` |
| power-off | `0x00013352` | `0x00004540` |

For settings, that pointer reaches a mode table containing a 32-bit count of
five followed by five far pointers. The common code selects:

- mode 1 for brightness;
- mode 4 for volume.

That exact numbering applies to the full five-mode G1/G2/SY table. It is not
a global resident enum.

The brightness mode contains four records, one for each logical brightness
level. The volume mode contains ten records. Each record is 14 words:

All five mode record counts match between G1 and SY:

```text
mode:          0  1  2   3   4
record count:  1  4  9  11  10
```

Only modes 1 and 4 have verified application-level meanings so far.

### Link-time compacted variants

An automatic scan found valid linked bundles in G1, G2, G3, G4, SY, and TM.
Five titles contain the recognizable settings bitmap graph:

| Title | Descriptor | Mode record counts | Brightness mode | Volume mode | First bitmap format |
|---|---:|---|---:|---:|---:|
| G1 | `0x0e` | `1,4,9,11,10` | 1 | 4 | `0x0b00` |
| G2 | `0x04` | `1,4,9,11,10` | 1 | 4 | `0x0500` |
| G3 | `0x14` | `4,10` | 0 | 1 | `0x1000` |
| G4 | `0x03` | `1,4,9,10` | 1 | 3 | `0x0900` |
| SY | `0x01` | `1,4,9,11,10` | 1 | 4 | `0x0800` |

Headless Ghidra decompilation independently confirms the generated mode
constants in G2, G3, and G4's volume/brightness handlers. The descriptor
schema and brightness/volume record counts are stable, but unused modes can
be omitted and later mode indices compacted. A homebrew asset builder must
therefore generate mode constants together with the bundle instead of
hard-coding resident-wide values.

| Record word | Observed value/role |
|---:|---|
| `0..1` | zero in all G1/SY settings records |
| `2` | `0x0014` |
| `3` | `0xfff0` (`-16`) |
| `4` | `0x0010` |
| `5` | `0xffdc` (`-36`) |
| `6` | `0x002c` brightness, `0x006b` volume |
| `7` | zero |
| `8..9` | `0xffffffff` sentinel |
| `10..11` | bundle-relative component-list pointer |
| `12..13` | bundle-relative pointer to a private two-word zero-initialized runtime slot |

The final slot pointers advance by exactly two words for every record in all
five settings-bearing titles, and every target is zero-initialized in the MBA.
The slots are mutable link-generated storage rather than stable lookup IDs.
The fixed fields, counts, and record stride match exactly between G1 and SY;
only pointer values relocate. The likely geometry/render meanings of words
`2..7` are deliberately left unnamed pending renderer analysis.

## Standard bitmap graph

Following settings-record words `10..11` recovers another common layer. The
target is a variable component list:

```text
u32 component_count
repeat component_count:
    s16 x_offset
    s16 y_offset
    u32 bitmap_descriptor_relative
```

Brightness records contain two components with X offsets `20` and `-20`.
Volume records contain three with X offsets `25`, `75`, and `-20`. G1 and SY
have identical list shapes and values; their relative bitmap addresses differ.
All corresponding Y offsets are zero. G3's different artwork uses brightness
X offsets `38,0` and volume offsets `0,43,93`, while retaining the same
component counts and bitmap geometry. Their alignment with the outer object
coordinates strongly identifies these as signed component positions.

Each referenced bitmap descriptor is six words:

| Word | Meaning |
|---:|---|
| `0` | resident bitmap format and sprite-palette selector |
| `1` | pixel width |
| `2` | pixel height |
| `3` | zero in the standard settings samples |
| `4..5` | bundle-relative pointer to chunk descriptors |

The first brightness bitmap is 48 by 32 pixels in both titles. Its chunk list
starts with a 32-by-32 chunk followed by a 16-by-32 chunk. A chunk is four
words:

| Word | Meaning |
|---:|---|
| `0` | width in low byte, height in high byte |
| `1` | flags/palette field; zero in the inspected settings chunks |
| `2..3` | normally a primary-storage-relative pixel-data pointer |

For these standard settings images, successive primary data offsets advance
by `width * height / 8` words, which is exactly two bits per pixel. Other
resource families use other format codes, so bits per pixel must still be
decoded from the outer format field rather than inferred from dimensions.

### Renderer-confirmed format word

Resident family-B draw routine `0x0591b0` follows setting-record words
`10..11`, iterates the four-word component references, and treats their target
as the six-word bitmap descriptor above. For every chunk, it:

1. passes the low byte of bitmap word 0 to `0x064186`;
2. passes the high byte to `0x064302`;
3. selects width/height exponents from the packed chunk dimensions;
4. supplies the chunk data pointer to the sprite graphics-address setter.

The two configuration routines write the same PPU sprite-attribute fields
used by the hardware renderer. This proves the following standard format:

| Bitmap word-0 bits | Meaning |
|---:|---|
| `7..0` | resident pixel-format code |
| `11..8` | four-bit PPU palette selector |
| `12` | select the additional `0x200`-entry sprite palette bank |
| `15..13` | not used by this family-B path in the inspected runtime |

Resident format codes `0`, `1`, and `2` select 2, 4, and 6 bits per pixel.
Codes `3..8` enter variants of the 8-bpp setup path. The standard
brightness/volume artwork always uses code 0.

The five title-specific settings values therefore select the following
palette slots while retaining the same 2-bpp artwork:

| Title | Format word | Palette selection | Default hardware index |
|---|---:|---|---:|
| G1 | `0x0b00` | selector 11, normal bank | `0x1b0` |
| G2 | `0x0500` | selector 5, normal bank | `0x150` |
| G3 | `0x1000` | selector 0, additional `0x200` bank | `0x300` |
| G4 | `0x0900` | selector 9, normal bank | `0x190` |
| SY | `0x0800` | selector 8, normal bank | `0x180` |

This is why the format word differs even though the pixels do not: palette
slots are assigned by each title's link and palette layout. It is not a
compression ID or title-specific bitmap encoding.

At all five selected slots, including G3's second half of the words-`4..5`
source, the titles contain the exact same four-word RGB555 sequence (SHA-256
`817656aab3728cb3f642450d7eb82341b886a667b341759a88d0cacf1bb565a5`).
The words are `0xb18c`, `0x0000`, `0x7fff`, and `0x4e73`. The first word has
bit 15 set and is transparent. This confirms that the standard artwork uses
the same four colors in every inspected title; both its linked pixel location
and linked palette slot are title-local.

Runtime memory capture and the newly recovered MBA page map establish the
standard settings chunks' 2-bpp packing:

```text
one byte = four row-major palette indices
bits 7..6 = first/left pixel
bits 5..4 = second pixel
bits 3..2 = third pixel
bits 1..0 = fourth/right pixel
```

Eight pixels occupy one little-endian u'nSP word: pixels 0..3 are in its low
byte and pixels 4..7 in its high byte. A 32-by-32 chunk is therefore exactly
256 bytes or 128 words, matching both pointer increments and live memory.

The clean-room C helpers pack/unpack one eight-pixel word.
`tools/assets/pack_bitmap_2bpp.py` converts an original four-index PGM into the same
byte layout. The public format helpers also construct/decode the pixel-format
code, palette selector, and extended-palette bit.

### Complete standard-settings payload census

The automatic graph walk now fingerprints every chunk used by all four
brightness records and all ten volume records. It finds 13 distinct payloads.
Every one of those 13 hashes occurs in all five titles, with identical bytes
and dimensions:

- 16-by-32 chunks;
- 32-by-32 chunks;
- 64-by-32 chunks.

This is direct evidence that the complete standard brightness/volume artwork
payload—not merely the first icon—came from a shared official SDK resource
set. Descriptor indices, lookup indices, relative pointers, and palette slots
remain title-local link results.

## What homebrew can reuse

The clean-room headers expose:

- the `0x20`-word header and proven word offsets;
- 10-word and 12-word raw descriptor layouts;
- the five standard setting modes and 14-word setting records;
- the four-word image-chunk lookup-directory entry;
- renderer-confirmed bitmap format, palette-bank, and 2-bpp packing helpers;
- word-pair read/write and relative-address helpers;
- target wrappers for bundle registration and both UI families.

Homebrew should create original graphics and sounds while using compatible
descriptors and runtime behavior. A standard-settings authoring path can now
emit an original two-mode family-B graph, all relocation classes needed by
that graph, both 512-entry palette sources, packed pixels, C arrays, and
generated mode constants. Runtime hardware validation of that generated graph
is still required before the authoring path can be considered verified.

## Reproducible evidence

- `research/reports/g1-vs-sy-asset-bundle.json` records addresses, counts, descriptor
  indices, and pointer metadata without storing asset contents.
- `research/reports/asset-bundle-catalog.json` records the automatic all-sample census,
  compacted mode mappings, all standard-settings graph nodes, and hashes for
  the 13 shared payloads.
- `tools/re/inspect_asset_bundle.py` parses the header, UI descriptors, and
  settings mode counts directly from an MBA.
- `tools/ghidra/ApplyMobiGoSdkNames.java` labels the common application
  runtime and bundle data in G1/SY.
- `tools/ghidra/FindInstructionScalars.java` reproducibly locates resident PPU
  and object-list code paths before targeted decompilation.
- Resident decompilation was performed against temporary runtime-memory
  imports outside this repository.
