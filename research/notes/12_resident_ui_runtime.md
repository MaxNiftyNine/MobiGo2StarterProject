# Resident UI runtime, family-A, family-B, and executable validation

Status: evidence-backed in emulator with the retail resident firmware

This note records the 2026-07-31 transition from static resource-format
reconstruction to executing newly authored resources through the actual MobiGo
resident runtime. All addresses are u'nSP 16-bit word addresses.

## Resident runtime capture

The emulator was booted with the retail internal ROM/SPI/NAND and used to dump
the live code/data window `0x050000..0x077fff`. The code image is retained at:

- `../MobiGo2StarterProject/build/resident_code_050000.bin`
- `../MobiGo2StarterProject/build/resident_data_050000.bin`

A persistent headless-Ghidra project lives under `build/ghidra-resident/`.
Selected resident implementations were decompiled from that captured image,
which avoids guessing service semantics solely from MBA call sites.

## Application lifecycle ABI

G1 entry `0x0e1a55` and the resident implementations independently establish
this official application skeleton:

1. service `0x075f46` performs application/framework setup;
2. service `0x075f48` executes one framework step;
3. service `0x075f4a` finalizes the framework.

`0x075f48` consumes a six-word callback table containing three far function
pointers in this order:

- start/init callback;
- per-frame callback;
- stop/cleanup callback.

This is exposed by `resident_runtime.h/.c` as
`struct mg_sdk_runtime_callbacks` and `mg_sdk_resident_runtime_setup/step/finalize`.

The older working label for `0x075f52` was wrong. Its implementation toggles
GPIO-B bit 9 around a short hardware-service sequence. It is now kept under the
neutral `MG_SDK_RESIDENT_SERVICE_075F52` name until the attached peripheral is
identified independently.

## Resident UI service family

The live trampoline bank maps these services:

| Service | Resident implementation | Recovered role |
|---:|---:|---|
| `0x075efa` | `0x055dec` | initialize family-A/B UI pools/state |
| `0x075efc` | `0x055f1b` | shut down family-A/B UI state |
| `0x075efe` | `0x055f84` | render/update UI families for the frame |
| `0x075f00` | `0x056820` | register/rebase linked asset bundle |
| `0x075f02` | `0x0569cf` | load family-A descriptor |
| `0x075f04` | `0x056a00` | initialize family-A descriptor runtime |
| `0x075f06` | `0x056a68` | create family-A object |
| `0x075f08` | `0x056a90` | destroy family-A object |
| `0x075f0e` | `0x056be3` | get family-A object storage |
| `0x075f10` | `0x056c15` | load family-B descriptor |
| `0x075f12` | `0x056c54` | create family-B object |
| `0x075f14` | `0x056ca4` | destroy family-B object |
| `0x075f18` | `0x056e7c` | get family-B object storage |
| `0x075f1c` | `0x056ffe` | bind/control family-B object |

Titles normally use the umbrella application lifecycle rather than invoking
`0x075efa/efc/efe` directly.

## Family-A linked image grammar

A family-A descriptor is ten words. Descriptor words `8..9` are a linked far
pointer to an 18-word image record. The resident renderer proves these fields:

| Image-record word | Meaning |
|---:|---|
| `0` | source/pixel width |
| `1` | source/pixel height |
| `2` | cell width |
| `3` | cell height |
| `4` | resident background-format selector |
| `10..11` | tagged background graphics-base pointer |
| `12..13` | tagged tilemap/index source pointer |
| `14` | background palette selector |
| `16..17` | bundle-relative private two-word mutable slot |

Words `5..9` and `15` remain unnamed. Across the inspected titles word `8` is
normally `width-1` and word `6` is normally `height-1`, but G1 contains a
counterexample with height 240 and word 6 equal to 303, so these are treated as
bounds/extents rather than renamed prematurely.

The renderer divides width by cell width and height by cell height, allocates a
resident tilemap, emits cells, sets the background format, graphics base, and
palette, then renders the object. Normal format codes `0..3` select tiled
2/4/6/8-bpp paths. The higher format family sets the PPU direct-colour control.

G1 family-A descriptor 7, used by application-requested shutdown, resolves to:

- 320 x 240 source;
- 16 x 16 cells;
- format 0 (2-bpp tiled);
- palette selector 10;
- a tilemap source dominated by tile index 1.

This makes family-A part of the shutdown backdrop/fade presentation rather than
an opaque animation blob.

`tools/re/catalog_family_a.py` catalogs the same grammar across G1/G2/G3/G4/SY/TM.
Current report totals are 34 descriptors, 28 non-null records, and 24 unique
non-null record images. See `research/reports/family-a-catalog.json`.

## Family-B descriptor and mutable object mapping

A family-B descriptor is twelve words. The loader copies it into the runtime
object with two inserted zero words:

- descriptor `0..5` -> object `0..5`;
- object `6..7` are reset to zero;
- descriptor word `6` -> object word `8`;
- descriptor word `7` -> object word `9`;
- descriptor `8..9` -> object `10..11`;
- descriptor `10..11` -> object `12..13` (nested graph pointer).

Renderer-backed object fields currently exposed are:

| Object word | Meaning |
|---:|---|
| `0` | visible/active gate |
| `1` | X anchor |
| `2` | Y anchor |
| `3` | presentation-specific state; settings use 0, requested-off uses 1 |
| `4` | orientation/coordinate-flip selector 0..3 |
| `5` | mode index |
| `6` | record index |
| `7` | animation stopped/frozen flag: zero advances, one freezes or marks completion |
| `8` | animation loop flag: zero stops on final record, nonzero wraps to record zero |
| `9` | opacity/intensity: 0 suppresses rendering, 1..0x3f blends, >=0x40 opaque |

The generic clean-room interface is `ui_family_b.h/.c`. The older
`settings_overlay.h/.c` API is retained as a settings-specific compatibility
wrapper over that generic object.

### Common family-B record grammar across the title corpus

`tools/re/catalog_family_b.py` follows every primary family-B descriptor in
G1/G2/G3/G4/SY/TM. All 147 descriptors parse successfully into 923 counted
modes and 6,822 14-word records; none require a title-specific grammar.

Resident preprocessing proves the record fields:

| Record word | Meaning |
|---:|---|
| `0` | signed X delta applied when advancing into this destination record |
| `1` | signed Y delta applied when advancing into this destination record |
| `2` | duration/tick span |
| `3` | signed minimum Y bound from object anchor |
| `4` | signed maximum Y bound from object anchor |
| `5` | signed minimum X bound from object anchor |
| `6` | signed maximum X bound from object anchor |
| `7` | reserved; zero in all 6,822 catalogued records |
| `8..9` | optional transition token; `0xffffffff` in all 6,822 catalogued records |
| `10..11` | counted component-list pointer |
| `12..13` | private mutable runtime-slot pointer |

1,434 records contain a nonzero movement delta. The most common durations are
100, 20, 200, 80, 160, and 40 ticks, confirming that this is the general
family-B animation/presentation record rather than a settings-only container.

The same census traverses 12,318 component references, 3,993 unique component
lists, 1,946 unique bitmap descriptors, and 4,232 bitmap chunks without a
structural failure. Across those unique bitmaps/chunks:

- bitmap descriptor word 3 is always zero;
- chunk word 1 is always zero;
- every chunk data pointer uses the primary `0x80000000` pointer class;
- bitmap format-code usage is 774 code-0 (2-bpp), 1,167 code-1 (4-bpp), and
  five code-2 (6-bpp) resources;
- no primary family-B bitmap in these six titles uses resident format codes
  3..8, although the renderer contains those 8-bpp paths.

The machine-readable evidence is `research/reports/family-b-catalog.json`.

`mg_sdk_ui_b_object_play_animation()` clears word 7 and selects loop behavior
through word 8. The resident can catch up across multiple expired records in a
single update. `make animation-check` runtime-verifies an original two-record
bundle advancing record `0 -> 1` and X `80 -> 84`, then stopping on the final
record.

## Header word 0x1a: auto-instance table

Header words `0x1a..0x1b` point to a two-part table indexed in flattened order:
all family-A descriptors first, then all family-B descriptors.

For `N = A_count + B_count` the storage is:

- `2*N` words of 32-bit markers;
- immediately followed by `2*N` words of 32-bit output handles.

Registration skips marker zero. For a nonzero marker it creates the matching
resident UI object and writes the returned handle into the parallel output
entry.

Cross-title evidence:

- G1/G2/G3/G4/SY have all-zero marker tables for the inspected primary bundle;
- TM sets family-A descriptor zero marker to `1`;
- a clean-room family-A bundle with marker 1 was registered in the emulator and
  the resident registrar wrote handle `0x90000000` into its output slot.

The table therefore requires four words per total UI descriptor even when all
markers are zero. Public helpers are in `resource_bundle.h/.c`.

## Boot-safe resource packaging rule

The first executable family-A experiment failed even though the linked graph
was structurally valid. The Generalplus compiler option `-mglobal-var-iram` had
placed a large writable BSS resource array starting at IRAM zero, overwriting
resident firmware state.

The working model is:

- keep the immutable bundle template and primary artwork as `const` executable
  data in the MBA;
- copy only the small linked bundle graph into writable title/application RAM;
- register that writable copy because service `0x075f00` rebases it in place;
- leave the large primary artwork in executable storage and pass its const base
  directly to the registrar.

The boot demos use word address `0x5000` as a proven writable application arena
and reserve status words near `0x58f0`. Retail titles also keep substantial
writable title state in the `0x5000` range. This is a proven emulator placement,
not yet a declaration that the whole range is universally free on hardware.

## Clean-room authored resources executed by the retail renderer

All artwork below is generated programmatically and contains no retail pixel
payload.

### Family-A background

`tools/assets/build_family_a_background_bundle.py` emits one 320x240, 16x16-cell,
2-bpp family-A background. Emulator execution returned family-A handle
`0x90000000` and rendered the authored pattern through the resident background
renderer.

Current generated size: 66 bundle words, 2,112 primary words.

### Brightness and volume

`tools/assets/build_standard_settings_bundle.py` emits one family-B descriptor with:

- brightness mode: four records;
- volume mode: ten records;
- fourteen original 64x32 2-bpp images.

Brightness emulator result:

- family-B handle `0x80000000`;
- non-black bbox `(77,201)..(136,229)`.

Volume emulator result:

- family-B handle `0x80000000`;
- non-black bbox `(111,207)..(166,223)`.

Current generated size: 506 bundle words, 4,608 primary words.

### Power-off presentation

G1 and SY independently use the same family-B graph shape:

- one mode;
- one 14-word record;
- one component;
- one 176x32 bitmap;
- bitmap chunks `64 + 64 + 32 + 16` pixels wide.

`tools/assets/build_poweroff_bundle.py` reproduces that graph with new artwork. At the
official `(160,120)` anchor the emulator returned handle `0x80000000` and the
non-black authored presentation occupied bbox `(79,107)..(234,132)`.

Current generated size: 98 bundle words, 1,728 primary words.

### Consolidated standard system UI

`tools/assets/build_system_ui_bundle.py` combines the common controls into one bundle:

- family-B descriptor 0: brightness + volume;
- family-B descriptor 1: power-off;
- 18 chunk-directory entries;
- two complete palette sources;
- one registration call for the whole standard UI set.

Current size: 572 bundle words, 5,312 primary words.

The end-to-end demo creates two objects from the same registered bundle:

- settings handle `0x80000000`;
- power-off handle `0x80000001`.

It renders brightness and power-off simultaneously. The exact clean-room frame
validation is:

- status `0x5004`;
- 320x240 frame;
- non-black bbox `(77,107)..(234,229)`;
- 1,161 non-black pixels;
- three authored non-black colours.

Run `make emulator-check` to rebuild the MBA, install it into a separate NAND
image, execute the resident runtime, and verify those values automatically.

## Validation commands

From the SDK repository root:

Run `make release-check` for the complete current host, target, emulator,
UI, input, storage, font, animation, effect, compressed-audio, and music suite.

## Remaining evidence boundary

The common UI/runtime is usable. Remaining unknowns are fields without an
independent consumer, EBOOK's absent external layout/font payload, secondary
storage controls, exact hardware identification for `0x075f52`, and physical
device validation of the chosen title-RAM placement.
