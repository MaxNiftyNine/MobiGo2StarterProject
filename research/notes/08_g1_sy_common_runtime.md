# G1/SY common-runtime comparison

`BUNDLE_G1_135800G1.MBA` and the system-menu application
`BUNDLE_SY_135800SY.MBA` were independently imported with the MBA loader and
analyzed as u'nSP code. Function candidates came from exact instruction-word
anchors, but every address below was corrected to a real function prologue
and verified by decompilation.

## Relocated common functions

| Clean-room name | G1 | SY | Cross-title result |
|---|---:|---:|---|
| `sdk_post_input_event` | `0x0dd19e` | `0x0d9e36` | Same event `0x1005`, routing fields, payload, and timestamp |
| `sdk_system_controls_init` | `0x0dd1fc` | `0x0d9e98` | Same persistent volume/brightness validation and overlay state |
| `sdk_input_and_system_controls_poll` | `0x0dd3cc` | `0x0da07e` | Same buffered/special/game/system ordering and timeout policy |
| `sdk_system_controls_shutdown` | `0x0dd632` | `0x0da340` | Same resident-object/context teardown role |
| `sdk_handle_volume_keys` | `0x0dd715` | `0x0da42d` | Same 0..9 logic, gains, positions, mode, and timing |
| `sdk_handle_brightness_key` | `0x0dd984` | `0x0da6a3` | Same 0..3 logic, backlight mapping, position, mode, and timing |
| `sdk_dispatch_touch_events` | `0x0df8fa` | `0x0dcf05` | Same four-word stride, x/y fields, `-1` sentinel, and callback ABI |
| `sdk_dispatch_game_key_edges` | `0x0df9a9` | `0x0dcfb1` | Same seven-entry mask/press/release table structure |
| `sdk_dispatch_buffered_input_codes` | `0x0dfa5c` | `0x0dd06d` | Same buffered-code and special-code translation structure |
| `sdk_dispatch_system_key_edges` | `0x0dfb49` | `0x0dd16b` | Same three-entry system-key/event table |
| `sdk_poll_high_level_input` | `0x0dfb86` | `0x0dd1a9` | Same combined dispatcher order |
| `sdk_runtime_init` | `0x0e0000` | `0x0de6f8` | Same resident application start-callback role |
| `sdk_runtime_tick_and_handoff` | `0x0e0075` | `0x0de770` | Same per-frame and cross-MBA handoff role |
| `sdk_update_poweroff_sequence` | `0x0e0211` | `0x0de8d6` | Same Off-key state machine and terminal service `0x075e5e` |
| `sdk_fill_words_far` | `0x0e15e5` | `0x0df6ed` | Byte-for-byte identical relocated function |

SY additionally exposes a clear stop callback at `0x0de8bd`, which releases
its resident runtime context. Its MBA entry at `0x0dfc1d` passes a six-word
callback descriptor at data-space address `0x5c75` to service `0x075f48`.
This independently confirms the descriptor recovered from G1.

## SY launching another MBA

A fresh loader import of SY confirms six direct calls to resident launch
service `0x075fca`. The selected-title helper at `0x0dda30` copies its packed
path, supplies one 32-bit argument with value `999`, and schedules the launch.
The per-frame wrapper at `0x0de770` performs title-specific cleanup, calls that
helper, clears its launch flag, and returns zero. SY entry `0x0dfc1d` then exits
the resident step loop, calls `0x075f4a`, and returns to its resident caller.

This establishes the complete transition contract independently of G1:

1. tear down title-owned runtime objects;
2. schedule the MBA with service `0x075fca`;
3. return zero from the active frame callback;
4. finalize through `0x075f4a`;
5. return from the MBA entry function.

Keeping the frame loop alive leaves the request pending. Spinning after
finalization also prevents the caller from completing the transition.

## Shared policy versus linked assets

The system-control behavior is source-level common code, but its feedback
sound resource IDs are not universal:

| Meaning | G1 resource | SY resource |
|---|---:|---:|
| setting changed | `0x20e4` | `0x20a8` |
| volume already maximum | `0x20e5` | `0x20a9` |
| power-off feedback | `0x20de` | `0x2062` |

The resident playback arguments otherwise match: gain `0x7f`, pan `0x40`,
flags zero, with mode selected by the caller. This means application builds
link or number their own sound resources even when the runtime source and UI
policy are shared.

The volume overlay remains mode `4`, logical level at object word `+6`, and
position `(109,214)` in both titles. Brightness remains mode `1`, word `+6`,
and position `(138,214)`. These fields are therefore SDK object semantics,
not G1-specific guesses.

The linked bundle now explains how those semantics reach presentation data.
G1 and SY use different family-B descriptor indices, but their settings and
power-off descriptors share the same 12-word template. Each settings
descriptor points to a five-mode table whose mode 1 has four 14-word records
and whose mode 4 has ten. The fixed record fields match between titles while
their resource pointers relocate. Full details are in
`research/notes/09_asset_bundle_runtime.md`.

## Reproducible artifacts

- `research/reports/g1-vs-sy-runtime-functions.json` contains raw locator candidates
  and scores. Candidate addresses are leads; the corrected table above is
  authoritative.
- `research/reports/g1-vs-sy-asset-bundle.json` contains recovered bundle metadata and
  the common settings descriptor shape.
- `tools/ghidra/ApplyMobiGoSdkNames.java` applies the verified G1 or SY names
  and comments to an analyzed program.
- `tools/ghidra/DumpInstructions.java` makes function-boundary correction
  reproducible without retaining proprietary decompiler output.

No retail executable bytes or extracted assets are stored in this project.
