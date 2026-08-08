# Public SDK headers

Include `mobigo_sdk/mobigo_sdk.h` for the complete public surface, or include a
focused header to keep dependencies explicit.

## Application and platform behavior

- `resident_runtime.h`: firmware-owned setup/step/finalize lifecycle.
- `application.h`: installed-path checks and asynchronous MBA launch requests.
- `memory_map.h`: supported title-RAM ranges and overlap helpers.
- `standard_controls.h`: canonical resident-lifecycle Volume/Brightness/Off
  integration with clean generated overlays.
- `direct_controls.h`: settings and power behavior for direct framebuffer
  loops; intentionally no resident overlay.
- `system_controls.h`: portable policy used by the two convenience adapters
  and host tests.
- `hardware.h`: target-only watchdog, inherited framebuffer, DMA, and 6×9
  matrix helpers. Raw MMIO remains private.

## Input, touch, audio, and storage

- `resident_keys.h`, `input.h`, `resident_input.h`: logical key state and event
  pumping.
- `touch.h`, `resident_touch.h`: portable touch records and resident queue.
- `audio.h`, `resident_audio.h`, `audio_resources.h`: playback state, resident
  playback calls, and W/S/M authoring.
- `resident_storage.h`: bounded resident file operations.

## Graphics and resources

- `resource_bundle.h`, `resource_graphics.h`: linked graphs, bitmap/chunk
  layouts, and address helpers.
- `resident_resources.h`: bundle registration and family-A/B object services.
- `settings_overlay.h`, `ui_family_b.h`: mutable UI records and animation
  authoring.

`resident_addresses.h` centralizes supported fixed resident entry points;
`resident_backend.h` binds the portable controls policy to them. Do not add a
guessed prototype merely because an address appears in research notes.

The maintained API guide starts at
[`docs/api/index.md`](../docs/api/index.md).
