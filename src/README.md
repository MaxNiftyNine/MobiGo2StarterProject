# SDK implementation

This directory contains original clean-room implementations corresponding to
the headers under `include/mobigo_sdk/`.

- Portable policy/authoring: `system_controls.c`, `input.c`, `touch.c`,
  `audio.c`, `audio_resources.c`, `resource_bundle.c`, `resource_graphics.c`,
  `settings_overlay.c`, `ui_family_b.c`, and `ui_family_b_animation.c`.
- Resident target adapters: `resident_backend.c`, `resident_input.c`,
  `resident_keys.c`, `resident_touch.c`, `resident_runtime.c`,
  `resident_audio.c`, `resident_storage.c`, `resident_resources.c`, and
  `application.c`.
- High-level controls: `standard_controls.c` for resident rendering and
  `direct_controls.c` for a framebuffer-owned loop.
- Low-level target helpers: `hardware.c` for watchdog, inherited buffers, DMA,
  and matrix access.

Portable modules must remain host-testable. Target adapters may use the fixed
resident surface exposed by public headers, but raw firmware code, retail
assets, and guessed calls do not belong here.
