# Dynamic bundles and clean-room text rendering

This note separates two related findings that should not be conflated:

1. a **resident dynamic asset-bundle facility**, implemented by the common
   firmware runtime and usable by homebrew; and
2. EBOOK's **title-local text/layout layer**, which consumes an external
   resource named `ft01` on top of that generic facility.

The first is now a recovered SDK API. The second is useful reference evidence,
but it is not currently claimed as a universal MobiGo text API.

## Resident dynamic bundle API

`USENG_EBOOK.MBA` calls three resident trampolines:

| Service | Resident target | Recovered role |
|---|---:|---|
| `0x075c52` | `0x0568be` | register dynamic v2 bundle |
| `0x075c54` | `0x05690b` | unregister dynamic bundle |
| `0x075c58` | `0x056c7c` | create family-B object from dynamic slot |

Direct resident decompilation proves that registration scans slots **1..7**.
Slot zero is the application's normal primary bundle. The dynamic registrar
relocates the same version-2 bundle grammar used by primary title assets, using
the caller's supplied primary-storage base. It returns zero when no dynamic
slot can be allocated.

Unregistration is not merely a table clear: resident code walks both UI object
families and destroys objects owned by the dynamic slot before releasing its
bundle state. `0x075c58` validates the requested dynamic slot and then reaches
the normal family-B object constructor.

The clean-room bindings are:

- `mg_sdk_resident_register_dynamic_bundle`;
- `mg_sdk_resident_unregister_dynamic_bundle`;
- `mg_sdk_ui_b_create_from_dynamic_bundle`.

The current resident-service census finds these three services used only by
`USENG_EBOOK.MBA` in the available MBA corpus. They are nevertheless resident
firmware facilities, not EBOOK implementations.

## EBOOK `ft01` behavior

EBOOK's resource layer indexes an external container as repeated records with
a four-byte key and 32-bit payload length. It searches for packed key `ft01`,
loads that payload into allocated RAM, registers it through `0x075c52`, and
creates glyph family-B objects from the resulting dynamic slot.

The glyph object path is especially useful for confirming family-B semantics:

- object word 5 selects one of EBOOK's font/style modes;
- object word 6 is set directly to the character code;
- object word 7 is set to one before display;
- normal object words 1/2 carry X/Y anchor coordinates.

EBOOK also has a separate per-character six-word layout/metrics layer used for
line/layout decisions and bounding calculations. Resident service `0x075f20`
transforms relative family-B record bounds into object-relative screen bounds,
respecting orientation.

The supplied stock NAND has `BOKSORT.LST = "0000\r\n"` and therefore no
installed book-content entry from which to recover the normal external `ft01`
payload. A transient direct EBOOK handoff is insufficient because the official
EBOOK entry receives launcher arguments and copies up to twenty 32-bit values
to `0x5000`; without a selected book those title-local resource fields remain
uninitialized/fill data. Consequently the six-word EBOOK layout format remains
title-layer work, not a blocker for the resident dynamic-bundle API.

## Family-B chunk-size constraint

The first clean font experiment used 8x8 2-bpp chunks. All pointers, glyph
payload bytes, record selectors, and live family-B objects were correct, but
the renderer sampled beyond the intended payload and produced unrelated
palette colors.

A new dimension census over all **4,232** unique primary family-B chunks from
G1/G2/G3/G4/SY/TM found only these axis sizes:

- 16 pixels;
- 32 pixels;
- 64 pixels.

All nine width/height combinations occur. No 8-pixel axis occurs.

Resident function `0x0591b0`, the family-B bitmap/sprite emitter, independently
confirms the rule: its PPU sprite-size programming has explicit branches only
for axis values `0x10`, `0x20`, and `0x40`. Unsupported values leave prior
sprite-size state intact, explaining the 8x8 over-read.

The public helpers `mg_sdk_bitmap_chunk_axis_supported` and
`mg_sdk_bitmap_chunk_dimensions_supported` now encode this recovered contract.

## Clean-room font

`tools/assets/build_clean_font_bundle.py` emits an original ASCII font bundle:

- one dynamic family-B descriptor;
- one mode;
- 128 records indexed directly by character code;
- original 5x7 block glyphs inside transparent **16x16** 2-bpp sprite cells;
- logical glyph bounds 6x8;
- six-pixel horizontal advance;
- static record duration 20 ticks.

The generated API can create individual glyphs or a NUL-terminated ASCII text
run. Text positions are deliberately described as **resident family-B anchor
coordinates**, not top-left pixels. Resident rendering center-anchors bitmap
chunks and applies the active PPU/global coordinate transform.

`make font-check` builds matched baseline/text MBAs with the real Generalplus
toolchain, boots both against the resident firmware, and compares frames. The
verified `HELLO 123` run produces:

- dynamic slot `1`;
- family-B handles `0x80000000` through `0x80000007`;
- 112 pixels changed relative to the matched no-glyph baseline;
- a 53x7 ink bounding box;
- every changed pixel black -> white, with no unrelated palette colors.

This is an end-to-end proof of original text artwork rendered through the
official resident dynamic-bundle and family-B paths.
