# Research log

## 2026-07-29: G1 baseline

Input:

- `../MBAs/BUNDLE_G1_135800G1.MBA`
- SHA-256
  `e2ae552854d5a9e91c7f66f88dcc867f61b777bf34b3e5887d98bb43cb2bdcf5`
- Runtime base `0x0c8000`
- Body load `0x0c8800`
- Entry `0x0e1a55`

### Initial architectural result

G1 has no conventional import table and contains more than a thousand
auto-discovered functions, consistent with substantial static linking.
However, it also calls a dense group of fixed addresses around
`0x075e00..0x075fff`, below the MBA mapping. These are candidate firmware or
resident-system service entry points and are likely the actual boundary
between an application runtime and the MobiGo operating environment.

The entry point:

1. initializes a small startup structure through `0x075f46`;
2. clears eight words at DS `0x5002`;
3. decodes flags and a far pointer from the launcher-provided argument block;
4. stores those values in DS `0x5000..0x5003`;
5. calls local configuration function `0x0dddcb`;
6. repeatedly invokes service `0x075f48` with value `0x5d1c`;
7. finalizes through service `0x075f4a`.

The official names and precise parameter types are not yet known.

### Cross-application launch helpers found in G1

G1 contains meaningful strings at:

| Address | String |
|---:|---|
| `0x0e20b9` | `A:\BUNDLE\SY\135800SY.MBA` |
| `0x0e20c6` | `MM.MBADEFAULT\MM.MBA` |
| `0x0e20d1` | `UB.MBADEFAULT\UB.MBA` |

Local function `0x0e0668` copies the SY path to a stack buffer and passes it
to resident service `0x075fca`. This is strong evidence that returning to the
system menu is an OS/application-chain operation rather than a framebuffer
asset embedded independently in each game.

Functions `0x0e07f4` and `0x0e08bb` perform nearly identical logic for
`MM.MBA` and `UB.MBA`:

1. query resident service `0x075fcc`;
2. construct a volume-qualified path through local helper `0x0e0782`;
3. test the resulting path through `0x075fb4`;
4. launch it through `0x075fca`;
5. fall back to `DEFAULT\MM.MBA` or `DEFAULT\UB.MBA`;
6. call `0x075f7c` if the prerequisite query fails.

This supports a split architecture:

- a statically linked application/game runtime;
- fixed resident services around `0x075xxx`;
- separate system-role MBAs for shared UI and lifecycle behavior.

### Early local function identifications

| Address | Working name | Confidence | Evidence |
|---:|---|---|---|
| `0x0e15e5` | `sdk_fill_words_far` | Strong | Writes one 16-bit value repeatedly for a 32-bit word count |
| `0x0dddcb` | `sdk_set_startup_flag` | Tentative | Sets one of three startup/configuration globals |
| `0x0e0668` | `sdk_return_to_system_menu` | Strong | Launches fixed SY MBA path |
| `0x0e0782` | `sdk_build_volume_path` | Strong | Prepends a resident-service-provided drive/path prefix |
| `0x0e07f4` | `sdk_launch_media_manager` | Strong | Resolves and launches `MM.MBA` |
| `0x0e08bb` | `sdk_launch_usb_app` | Strong | Resolves and launches `UB.MBA` |

Names are descriptive clean-room names, not claimed official SDK symbols.

## 2026-07-29: exact cross-image comparison

`tools/re/find_exact_shared_blocks.py` compares MBA/GAM bodies as 16-bit words,
then verifies every reported rolling-hash match byte for byte. The current
G1-to-all report is `research/reports/g1-vs-all-exact.json`.

All comparisons contain relocated exact matches: no long match retained the
same runtime address. This confirms that common material is being linked or
packed into each image independently rather than imported at one fixed
application address.

The amount of exact material varies substantially:

| Target | Exact shared bytes |
|---|---:|
| G2 | `0x77638` |
| G4 | `0x2e962` |
| SY | `0x1f3b4` |
| G3 | `0x1d3b0` |
| MM | `0x7ed2` |
| UB | `0x5eb2` |
| TM | `0x3f88` |
| GAM 029 | `0x5d4c` |

Smaller exact totals do not disprove source-level reuse: absolute references,
compiler options, patched constants, or different library versions can break
byte equality.

The word-fill routine identified in G1 at `0x0e15e5` is inside an exact block
that maps to SY runtime address `0x0df6ed`. This is the first function-level
proof of common statically linked runtime code. It should be named and traced
after SY is loaded into the connected Ghidra session.

## 2026-07-29: shared `SPF2ALP` sound-patch bank

An exact `0x34b8`-byte block at G1 file offset `0x6e46c` (runtime word address
`0x0ff236`) is present byte for byte in twelve other inspected applications:
G2, G3, G4, SY, TM, EBOOK, MM, UB, and all four numbered GAM samples. LD is
the exception; it contains a much smaller, different set of `SPF2ALP`
records.

The block SHA-256 is:

```text
4942eaad03a9e63410e46111328d878d727a56a8d21acbf82074d6282acdf92c
```

The earlier possibility that this was a font or sprite resource has been
rejected. Its verified structure is:

- 71 primary patch groups;
- 34 secondary patch groups;
- 158 total zones;
- one to four zones per group;
- a group header of `8 + 4 * zone_count` bytes;
- a table of zone offsets in `0x44`-byte increments;
- fixed `0x44`-byte zones, all containing the eight-byte tag
  `SPF2ALP\0`;
- low/high key-range bytes at the start of each zone;
- playback values including the standard audio rates 8000, 11025, 16000,
  and 22050.

Related `SPF2ALP` records in the resident SPI image place `0x2b11` (11025)
beside byte/sample counts with an approximately 2:1 relationship. Together
with the key ranges, this is strong evidence for a Generalplus sound-patch or
instrument-bank format.

The precise semantics of most zone fields, the relationship to waveform
payloads, and the official meaning of `SPF2ALP` remain unknown. The
clean-room parser therefore exposes unresolved fields as raw values rather
than assigning speculative SDK names.

Artifacts:

- `tools/re/inspect_spf2alp_bank.py`
- `research/reports/g1-shared-spf2alp-bank.json`
- `research/reports/shared-spf2alp-instances.json`

The G1 data at `0x0ff236` has been labeled
`shared_spf2alp_sound_patch_bank` and commented in Ghidra.

## 2026-07-29: common volume, brightness, and Off subsystem

A batch decompilation of G1's high-address runtime found the complete common
system-controls layer. The functions have been renamed and commented in
Ghidra:

| Address | Clean-room name |
|---:|---|
| `0x0dd1fc` | `sdk_system_controls_init` |
| `0x0dd3cc` | `sdk_input_and_system_controls_poll` |
| `0x0dd632` | `sdk_system_controls_shutdown` |
| `0x0dd715` | `sdk_handle_volume_keys` |
| `0x0dd984` | `sdk_handle_brightness_key` |
| `0x0e0000` | `sdk_runtime_init` |
| `0x0e0075` | `sdk_runtime_tick_and_handoff` |
| `0x0e0211` | `sdk_update_poweroff_sequence` |

The runtime uses ten logical volume levels mapped to resident gains
`{4,14,25,35,45,55,67,79,91,105}` and four brightness levels mapped to
`{1,5,10,15}`. Exact adjacent copies of both tables occur in every inspected
full runtime except the small LD and TM applications.

The key masks are `0x0400` volume up, `0x0800` volume down, `0x1000`
brightness, and `0x0200` Off. The status UI is an opaque resident object type
`0x0e`; mode 4 displays volume at `(109,214)` and mode 1 displays brightness
at `(138,214)`. The Off sequence may show object type `0x30` at `(160,120)`,
plays sound `0x20de`, and ends by calling resident service `0x075e5e`.

Full details and evidence are in `research/notes/01_system_controls.md`.

## 2026-07-29: resident-service ABI and cross-image census

The two-word u'nSP far-call encoding used for fixed resident services has
been reproduced by the Generalplus compiler used for target builds. With its 32-bit pointer
model, calling an absolute C function pointer such as `0x00075eaaUL` emits
the expected `R3 = 0x5eaa`, `R4 = 7`, `call MR` sequence. A target-only
system-controls adapter now compiles and assembles successfully.

`tools/re/catalog_resident_calls.py` also scanned all 14 current samples for
direct calls into `0x075c00..0x075fff`. The repeated service addresses
confirm that this is a stable resident API bank rather than a G1-specific
accident. For example, `0x075e5e` occurs in 8 images, the common startup
entries `0x075f46`, `0x075f48`, `0x075f4a`, and `0x075f52` each occur in
8, and UI-object accessor `0x075f18` has 462 raw calls across 8 images.

Raw scans can mistake data for instructions, so important call sites still
require Ghidra verification. See `research/notes/02_resident_services.md` and
`research/reports/resident-service-calls.json`.

## 2026-07-29: resident module captured and decoded

Booting the stock firmware in the existing emulator and capturing runtime
word memory proved that `0x075c00..0x075fe0` is a 496-entry far-`GOTO`
trampoline table. All entries decode correctly: 285 dispatch to real
implementations in `0x055dec..0x06d579`, while 211 unsupported ABI slots jump
to themselves.

A temporary raw Ghidra import seeded every trampoline and implementation
target. Direct decompilation confirmed the input-state tests, settings
getters/setters, tick counter, UI-object dispatch, path testing, and MBA
launch implementation. The launcher at service `0x075fca` accepts a far path
pointer, a count clamped to 16, and a far pointer to 32-bit arguments; it
copies at most 42 path bytes and schedules an asynchronous handoff.

No captured firmware body or decompiler listing is retained in this
clean-room tree. The address-only result is
`research/reports/resident-service-targets.json`; reproducible scripts are under
`tools/ghidra`.

## 2026-07-29: exact key-edge and touchscreen APIs

Decompilation of both resident key-state families corrects an earlier
“stable/debounced” interpretation. Their update routines store:

```text
changed = old_current XOR new_current
current = new_current
```

The system-key services are `0x075e60` current mask, `0x075e62` down,
`0x075e64` pressed edge, and `0x075e66` released edge. The parallel
game-control services are `0x075ec6`, `0x075ec8`, `0x075eca`, and
`0x075ecc`. The target SDK now exposes all eight query operations, while the
common G1 event pump intentionally uses pressed edges.

G1 also identifies a separate touchscreen queue at resident services
`0x075f3a` (far record pointer) and `0x075f3c` (record count). Local function
`0x0df8fa` iterates all records at a four-word stride, consumes signed x/y
from words 0/1, and derives state 2 when either coordinate is `-1`, otherwise
state 0. Words 2/3 are not interpreted by that dispatcher and remain exposed
as raw values in the clean-room API. See `research/notes/06_ui_touch_runtime.md`.

The same resident analysis recovers the application lifecycle behind
`0x075f46`, `0x075f48`, and `0x075f4a`. A six-word descriptor contains
32-bit far pointers to start, frame, and stop callbacks. The resident step
updates system keys, timers/events, audio, game keys, touch, and other device
facilities before calling `frame(ticks)`. The clean-room target API now
provides the exact descriptor and standard setup/step/finalize loop. See
`research/notes/07_application_runtime.md`.

## 2026-07-29: independent G1/SY runtime confirmation

SY was imported into a separate temporary Ghidra project with the MBA loader.
Instruction anchors located the common-runtime copies; each reported address
was then corrected to a real u'nSP function prologue and decompiled.

The system-controls, event posting, touch queue, game-key edge dispatch,
buffered input, system-key dispatch, resident start/frame lifecycle, Off
sequence, and far word-fill implementations all have verified counterparts.
The touch dispatcher is semantically identical, including its four-word
record stride and state-2 `-1` sentinel. SY's entry also passes the same
three-far-callback descriptor to resident service `0x075f48`.

The comparison proves that presentation behavior is common source code while
resource numbering is application-linked. SY uses sound IDs `0x20a8`,
`0x20a9`, and `0x2062` where G1 uses `0x20e4`, `0x20e5`, and `0x20de`.
Object field offsets, display modes, coordinates, level ranges, gain/pan
arguments, and timeout policy remain the same. Full addresses and evidence
are in `research/notes/08_g1_sy_common_runtime.md`.

## 2026-07-29: linked bundle, common UI, and bitmap graph

Resident service `0x075f00` is now identified as the linked asset-bundle
registrar/relocator. G1's header is at word address `0x0e2160`; SY's is at
`0x0f30ba`. Both use a `0x20`-word header, 10-word family-A descriptors,
12-word family-B descriptors, and three pointer classes: bundle-relative,
primary-storage-relative (`0x80000000` tag), and secondary-storage-relative
(`0xc0000000` tag).

G1 and SY's settings and power-off objects use identical family-B descriptor
templates despite different descriptor indices. Their settings resources
both have five modes with record counts `{1,4,9,11,10}`. Brightness is mode
1 and volume is mode 4. Every setting record is 14 words.

The all-sample bundle census later showed that these mode numbers are
link-generated rather than resident-global. G2 uses the same five modes, G4
compacts the table to `{1,4,9,10}` (brightness 1, volume 3), and G3 compacts
it to `{4,10}` (brightness 0, volume 1). Headless decompilation of all three
handler pairs confirms the remapped constants.

Following the standard settings graph recovered a counted component list,
six-word bitmap descriptors, and four-word bitmap chunks. The first
brightness bitmap is 48x32 in both titles and is composed from 32x32 and
16x32 chunks whose pixel pointers use the primary-storage tag. G1/SY
structure and geometry match while their linked addresses and format words
differ.

Clean-room headers, target service wrappers, host tests, a metadata inspector,
and Ghidra data annotations now cover this recovered surface. See
`research/notes/09_asset_bundle_runtime.md`.

## 2026-07-29: physical page map and shared SDK artwork

The `0x240`-byte launcher footer contains a 52-dword physical page-load
bitmap beginning at file offset `0x0dd8`. One bit represents `0x800` runtime
words or one `0x1000`-byte file page. The loader consumes file pages while
visiting set bits in ascending order. Across every MobiGo 2 sample,
the bitmap population count exactly equals the file page count.

This proves that the apparent linear MBA body is actually compacted. G1 maps
its first 120 pages at `0x0c8000` and its remaining 412 pages at `0x31b000`;
SY maps 110 pages at `0x0c8000` and 262 at `0x366000`. G2/G3/G4 use the same
two-run scheme. Their primary run starts exactly at the far pointer passed to
resident bundle-registration service `0x075f00`, and all five primary runs
end at `0x3e9000`.

Stock SY runtime tracing observed the firmware's page-by-page DMA copies.
The first standard brightness chunk resolved to physical address `0x37ae60`
and matched file offset `0x097cc0`, satisfying
`0x06e000 + 2 * 0x14e60`. The complete 256-byte 32-by-32 chunk is identical
in G1, G2, G3, G4, and SY, directly confirming shared official SDK artwork.

Visual bit-order testing establishes four row-major 2-bit indices per byte,
most-significant pair first. The clean-room SDK now has C packing helpers and
an original-PGM offline packer. The Ghidra 11.3.2 loader decodes the footer,
maps code and primary assets at their physical addresses, and retains a
legacy linear fallback. See `research/notes/10_mba_page_load_map.md`.

## 2026-07-29: complete settings artwork and renderer format

Recursive traversal of all four brightness records and all ten volume records
found 13 distinct pixel payload hashes. Every hash is present byte-for-byte in
G1, G2, G3, G4, and SY. This proves that the entire standard settings artwork
payload is shared official SDK material, not only the first brightness icon.
Lookup-directory indices, descriptor indices, and linked addresses differ by
title.

Resident family-B renderer `0x0591b0` consumes the recovered six-word bitmap
descriptor directly. It passes the format word's low byte to `0x064186` and
its high byte to `0x064302`, then programs dimensions and the chunk graphics
address. The low byte selects 2/4/6/8-bpp resident paths. High-byte bits 3..0
select the PPU palette and bit 4 selects the additional `0x200` palette bank.
Thus G1/G2/G3/G4/SY values `0x0b00`, `0x0500`, `0x1000`, `0x0900`, and
`0x0800` are title-local palette assignments for the same 2-bpp graphics.

Clean-room C helpers now encode and decode this format field. The generated
asset catalog schema 3 contains the full graph and all shared payload uses.

## 2026-07-29: palette closure and clean-room settings authoring

Version-2 registration path `0x065fb2` calls palette loader `0x065ec8`.
Header words 2 and 4 each identify 512 RGB555 entries: their halves populate
hardware banks `0x000/0x200` and `0x100/0x300`. This resolves G3's apparent
high-bank exception. All five games select the same four RGB555 colors,
including G3 at hardware slot `0x300`.

Every settings record's words 12..13 point to a private two-word
zero-initialized slot. Those pointers advance by two words in every inspected
title, removing the earlier “linked lookup value” ambiguity.

`tools/assets/build_standard_settings_bundle.py` now emits an original two-mode
version-2 graph, two complete palette sources, 14 programmatically drawn 2-bpp
images, binary and C forms, generated constants, previews, and a manifest.
None of its pixel hashes matches the official settings payloads. Host tests
pass and the generated resources compile with the Generalplus toolchain.
Runtime registration/rendering remains unverified.

G1's volume and brightness handlers also confirm family-B object word 0 as
visibility, words 1/2 as X/Y, word 5 as the bundle-local mode, and word 6 as
the selected record. These fields are exposed by
`mobigo_sdk/settings_overlay.h` and annotated in the connected Ghidra program.
