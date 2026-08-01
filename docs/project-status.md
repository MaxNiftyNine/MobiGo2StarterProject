# Project status and final handoff

Last updated: 2026-08-01

This repository is a clean-room reconstruction of the common MobiGo/MobiGo 2
application runtime, linked-resource environment, and practical homebrew build
surface used by official MBA applications.

## Executive status

The original hypothesis is confirmed. Official applications share a resident
runtime and a common resource/audio grammar. Descriptor numbers, linked offsets,
and artwork/audio payloads are title-local, but the APIs, object models,
registration rules, system controls, lifecycle, storage calls, graphics graphs,
and sound/music engines are common.

The repository now provides a usable development environment rather than only
format notes:

- real Generalplus u'nSP C/assembler/linker builds natively on Windows and
  through Wine on macOS/Linux;
- deterministic code and initialized-resource section alignment in the unified
  application builder, independent of source-file count;
- complete clean MBA packaging for G1 and SY slots;
- resident application lifecycle, input, touch, system-control, storage,
  graphics, dynamic-bundle, sound, and music bindings;
- original family-A backgrounds and family-B UI/sprite/animation generators;
- original dynamic ASCII text rendering;
- original PCM8 and ADPCM36 effects;
- original sequenced M music with melodic programs, upper-key zones, direct
  percussion, envelopes, and automatic SPU beat scheduling;
- reproducible host, target, and retail-resident emulator regressions.

The from-scratch G1/SY MBA construction path has also been reported working on
physical MobiGo 2 hardware. The broader SDK audit below distinguishes that
confirmed container/launch result from subsystems that have only been exercised
against the resident firmware in the emulator.

No additional MBA needs to be loaded in Ghidra for the current SDK surface.
Persistent headless projects and local G1/G2/G3/G4/SY/TM/EBOOK evidence cover
the common runtime. The remaining limitations are external-evidence or physical
hardware questions, listed at the end of this file.

## Recovered resident ABI

The public clean-room bindings include:

- application setup / step / finalize (`0x075f46/48/4a`);
- start/frame/stop callback table and firmware-owned frame pump;
- current/down/pressed/released key and system-key queries;
- four-word touch queue and input-event posting;
- logical volume and brightness get/set plus hardware application;
- power-off request;
- version-2 asset registration and seven dynamic bundle slots;
- family-A and family-B load/create/destroy/get operations;
- resident UI initialization and frame rendering;
- packed-path storage open/close/read/write/truncate/seek/size/stat/remove/type;
- W/S effect playback and state;
- M music play/pause/resume/stop/state/repeat/level;
- title audio/patch registration.

`0x075f52` is not application initialization. It performs a GPIO-B bit-9
peripheral sequence. Its exact attached hardware function remains unidentified.

## Application and memory model

A direct MBA entry patched to `main()` does not perform a normal initialized
mutable-data copy. Large mutable globals also cannot safely use the compiler's
default low-IRAM placement because resident firmware owns that space.

The verified packaging model is:

1. keep immutable templates, pixels, and waveforms as `const` executable data;
2. copy only mutable linked graphs into caller-selected title RAM;
3. register the writable graph, which the resident rebases in place;
4. pass const primary/waveform storage directly;
5. run through the recovered resident lifecycle.

The regressions use word address `0x5000` as a title-RAM arena. The guided suite
has now exercised this placement on physical hardware for registered graphics,
text, animation, state, and generated audio resources.

## System controls

Recovered and executable behavior includes:

- ten volume levels (`0..9`);
- four brightness levels (`0..3`);
- pressed-edge handling and hold suppression;
- common overlay timing;
- maximum-volume feedback;
- application-requested and physical-Off shutdown paths;
- shutdown sound wait and final resident power request.

Generated original brightness, volume, and power-off resources reproduce the
common interaction using no retail artwork.

## Linked graphics environment

### Version-2 bundle

The mutable header is `0x20` words and begins with `0x80000002`. Recovered
pointer classes and tables include:

- bundle-relative pointers based at `header + 0x20`;
- primary `0x80000000` pointers;
- secondary `0xc0000000` pointers;
- two 512-word RGB555 palette windows;
- family-A and family-B descriptor tables;
- bitmap lookup entries;
- header `0x1a` auto-instance marker/output-handle table.

For `N = A_count + B_count`, the auto table stores `2*N` marker words followed
by `2*N` output-handle words. Runtime proof produced family-A handle
`0x90000000` from a nonzero marker.

### Family-A

The recovered graph is a 10-word descriptor pointing to an 18-word tiled-image
record containing dimensions, cell dimensions, PPU format, tagged graphics and
tilemap pointers, palette selector, and a private runtime slot.

`research/reports/family-a-catalog.json` covers 34 descriptors, 28 non-null records, and
24 unique records across G1/G2/G3/G4/SY/TM. Original family-A output is generated
by `tools/assets/build_family_a_background_bundle.py` and rendered by the resident.

### Family-B

The common graph is:

```text
12-word descriptor
  -> counted modes
     -> counted 14-word records
        -> counted component references
           -> 6-word bitmap descriptors
              -> 4-word chunks
```

Recovered record fields include destination X/Y delta, duration, bounds,
optional transition token, component pointer, and private runtime pointer.
Legal observed chunk axes are 16, 32, and 64 pixels; all nine combinations
occur. Pixel format codes 0/1/2 are 2/4/6 bpp.

The mutable object words now have executable semantics:

- word 0: visible;
- words 1/2: X/Y anchor;
- word 3: presentation state;
- word 4: orientation/flip;
- words 5/6: mode/record;
- word 7: animation stopped (`0` running, `1` frozen/finished);
- word 8: animation loop (`0` stop on final record, nonzero wrap);
- word 9: opacity/intensity.

`mg_sdk_ui_b_object_play_animation()` starts the resident timeline. The resident
can consume multiple expired records in one update, applies the destination
record's delta, and either stops or wraps according to word 8.

`research/reports/family-b-catalog.json` validates 147 descriptors, 923 modes, 6,822
records, 12,318 component references, 1,946 unique bitmaps, and 4,232 chunks.
The original two-frame animation regression advances record `0 -> 1` and X
`80 -> 84` through the retail resident engine.

Public authoring constructors cover records, components, bitmaps, and chunks.
Generators cover settings, power-off, combined system UI, clean fonts, and a
reference animation.

## Dynamic bundles and text

Resident service `0x075c52` registers one of seven dynamic slots; `0x075c54`
unregisters and destroys owned objects; `0x075c58` creates family-B objects from
an explicit slot. EBOOK is the observed retail consumer, but the capability is
generic.

The clean font generator emits original 5x7 glyph art in legal transparent
16x16 family-B cells. `make font-check` verifies dynamic slot 1, glyph handles,
a 112-pixel footprint, 53x7 geometry, and expected black-to-white rendering.

EBOOK additionally uses a title-local six-word layout/metrics block and external
resource key `ft01`. The stock NAND contains no installed book payload, so that
container and its proportional metrics cannot be recovered from the available
files.

## Audio environment

### Registration and resource classes

`0x075e06` registers:

1. the title M/W/S resource root;
2. the melodic/percussion patch root used by M notes.

The first root starts with three 32-bit counts followed by M, W, and S resource
pointers and a terminal waveform-layout pointer. Local resource IDs begin at 3.

- **W**: fixed 32-word single-waveform resource.
- **S**: 10-word header plus ordered child IDs and `0xffffffff`; the same voice
  advances through children, and the fifth play argument is repeat/loop.
- **M**: 10-word header plus compact MIDI-derived 16-bit commands.

### M command grammar

The complete resident dispatcher is represented by public writers:

- `0x0`: note `(channel, note, velocity, duration)`;
- `0x1`: short/extended wait;
- `0x2`: consume and discard one following word;
- `0x3`: MIDI Control Change;
- `0x4`: Program Change;
- `0x5`: opaque low-byte metadata marker;
- `0x6`: end/repeat;
- `0x7cNN`: consume a control word, copy `NN` inline words to scratch `0x0397`,
  and optionally call a title callback for channel `c`;
- `0x80NN`: copy `NN` inline words to scratch `0x0397` without the callback.

The inspected G1/G2/SY songs parse without desynchronization. The auxiliary
classes are independently runtime-verified with final scratch words
`0x9abc/0xdef0`.

### Patch banks and original music

The second root supports:

- multiple melodic program directory entries;
- multiple ordered upper-key zones per program;
- direct-note percussion entries for channel 9;
- root-key transposition;
- sample, loop, and envelope offsets;
- PCM8 and ADPCM36 zone selectors.

The clean format setter uses codec byte `0xd0` for resident internal format 5
ADPCM36. Retail zones usually contain `0xd4/0xd5`; their additional low bits are
control flags, not required to select the codec.

### ADPCM36

The SPU stream is:

```text
frame = one header word + eight nibble-data words = 32 samples
stream end = dummy header word + 0xffff data sentinel
```

The header low nibble is a right shift and bits 4..9 are a signed first-order
predictor coefficient. The SDK includes a small predictor-zero target encoder.
`tools/assets/build_adpcm36_audio.py` provides an offline adaptive encoder that searches
all signed coefficients and shifts, emits deterministic C/header/binary/JSON,
and writes a decoded WAV preview.

Generated ADPCM36 is verified through both W effects and M music zones.

### Automatic SPU beat scheduling

The resident music initializer at `0x06286a` programs SPU beat registers and
installs callback `0x062de2`. The emulator directly models:

- beat base `0x7b84`;
- beat count/status `0x7b85`;
- Status3 bit 2 and Priority3 bit 2;
- normal IRQ4 and optional FIQ routing;
- zero-count minimum heartbeat;
- stop/status and channel reconfiguration semantics needed by the resident.

The implementation lives in `emulator/src/audio.hpp` and `emulator/src/bus.hpp`,
with regression coverage in `emulator/tests/audio_test.cpp`. The regular
emulator builder compiles this source and can run CTest with `--test`. Homebrew
music no longer calls an internal resident tick manually.

Physical-console testing on 2026-08-01 confirmed audible homebrew PCM/S/ADPCM
and M playback. It also showed that the resident audio query/control return
registers cannot be treated as portable success booleans. The hardware suite
now validates returned handles and written state/level/aux values, with a
bounded listening fallback for short effects.

Runtime music proof:

- four sequential M handles `0x40000004..0x40030004`;
- program 0 lower and upper zones, program 7, and percussion note 36;
- pitches `0x1d1d/0x2bab/0x3a3a/0x2464`;
- automatic IRQ4 completion frames `16/31/47/62`;
- generated ADPCM36 music mode `0xf38e`, format register `0xbe00`, pitch
  `0x0747`, velocity/pan `0x4064`, state `2 -> 0`.

## Storage

The public path wrapper packs two ASCII bytes per 16-bit word, matching the
resident ABI. Existing-file operations are runtime-verified against copied NAND
images: open, size, read, seek, truncate, overwrite, close/reopen, reread,
remove, and generation handles.

The resident reaches a real low-level allocation path for a missing pathname,
but the current NAND/FTL model does not publish a newly created directory entry
that remains discoverable after close. Physical hardware or a more faithful FTL
model is required to decide whether the remaining issue is emulator behavior or
an undiscovered publication call.

The first physical hardware-suite run also failed its fresh-file transaction
and its separate fresh relaunch-marker transaction. Because those screens did
not expose the exact failed storage phase, this is corroborating evidence, not
a precise localization of the publication defect. The on-device suite is now
non-destructive and reads `A:DEGER\\MBASORT.LST`; copied-NAND regressions retain
write, truncate, and remove coverage.

A follow-up relaunch run reached the pending-handoff timeout. This confirmed
that scheduling alone is insufficient while a title continues returning one
from its frame callback. The corrected suite follows G1: schedule the launch,
return zero from the callback, leave the resident step loop, and finalize. A
second run then froze because the direct homebrew entry spun after finalization.
Fresh SY decompilation closed the remaining contract: SY tears down its title
objects, passes one argument `999`, returns zero from its frame, finalizes, and
returns from the MBA entry. The suite now matches that complete sequence.

## Build and validation

### Independent audit (2026-08-01)

The continuation was reviewed as untrusted source before publication. The audit
found and repaired five defects: the font regression had an unnecessary Pillow
dependency; failed multiword M-event writes could leave partial commands in a
full buffer; and the Ghidra extension declared an incompatible fixed host
version. Publication testing also found that one host test silently depended on
a private retail-sample directory, and that devkitPro's `pkg-config` could
shadow the Homebrew executable that provides SDL2 metadata. Public CI now falls
back to the checked-in evidence catalog when samples are absent; the writer
preflights capacity; the loader uses Ghidra's build-time extension version
token; and the emulator builder selects a `pkg-config` that resolves SDL2.

The audited tree passed:

- all nine host C executables and 19 Python test cases;
- the host C suite under AddressSanitizer and UndefinedBehaviorSanitizer;
- all 26 SDK/generated-resource modules with the Generalplus target compiler,
  with zero C/assembly errors or warnings;
- a clean application MBA build with no source application container;
- the Ghidra 11.3.2 extension build plus a successful headless auto-import of
  that generated MBA as `unsp:LE:16:default`, with the two footer page-map runs
  and valid header CRC reported by the loader;
- clean emulator build and its three CTests;
- framebuffer/RAM checks for system UI, input, storage, dynamic text, family-B
  animation, PCM8, ADPCM36, multi-zone music, ADPCM36 music, and M auxiliary
  commands.

The linker emits one expected warning about application-owned interrupt symbols
not being present in direct-main probes. Resident firmware owns those vectors.

The single release command is:

```sh
make release-check
```

It serially runs:

```text
host C + Python tests
Generalplus target compilation
emulator build + CTest
system UI rendering
live system-key input
storage
font/dynamic text
family-B animation
PCM8 W
ADPCM36 W generated from WAV
PCM8 M multi-zone/program/percussion
ADPCM36 M generated from WAV
M auxiliary block commands
```

Individual targets remain available: `test`, `target-check`, `emulator-test`,
`emulator-check`, `homebrew-check`, `storage-check`,
`font-check`, `animation-check`, `audio-check`, `adpcm-check`, `music-check`,
`music-adpcm-check`, and `music-aux-check`.

The linker body warns that interrupt-vector symbols are undefined in direct-main
probes. Applications intentionally rely on resident firmware vectors; this is a
body-file warning, not a C/assembly failure.

## Ghidra and reproducible RE

The MBA/GAM extension creates the recovered page mappings, hardware ranges,
entry points, and symbols during import. Reusable scripts under
`tools/ghidra/scripts/` provide selected decompilation, xrefs, instruction ranges, and
word reads. Generated reports and name seeds preserve the recovered service map
without requiring the original analysis projects.

## Remaining external/evidence blockers

The common homebrew SDK/runtime reconstruction is usable. These items cannot be
closed honestly from the available evidence alone:

1. continued physical MobiGo 2 validation of shutdown, the revised asynchronous
   self-relaunch check, and audio state/control behavior across revisions (the
   title-RAM arena, graphics/input, and audible homebrew audio now have direct
   hardware evidence);
2. EBOOK's absent external `ft01` book/font payload and title-local proportional
   metrics;
3. exact peripheral attached to GPIO-B bit 9 in service `0x075f52`;
4. new-file directory publication on physical NAND or a fully faithful FTL;
5. names/semantics for remaining rarely consumed descriptor, envelope, and
   secondary-storage control fields where no independent caller exists.

These are explicit evidence boundaries, not unfinished implementation of the
common APIs demonstrated by the release suite.

## Reading order

1. `README.md`
2. `docs/getting-started.md`
3. `docs/project-status.md`
4. `research/notes/12_resident_ui_runtime.md`
5. `research/notes/13_resident_storage.md`
6. `research/notes/14_dynamic_bundles_and_text.md`
7. `research/notes/15_audio_resources_and_music.md`
8. `research/reports/family-a-catalog.json`
9. `research/reports/family-b-catalog.json`
