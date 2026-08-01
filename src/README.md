# Clean-room runtime

Original homebrew implementations:

- `system_controls.c`: portable implementation of the recovered system-control
  behavior.
- `resident_backend.c`: target-only fixed-address service adapter; currently
  excludes unverified resident overlay and feedback-sound calls and uses the
  centralized constants in `include/mobigo_sdk/resident_addresses.h`.
- `application.c`: target-only wrappers for resident path testing and MBA
  handoff.
- `input.c`: portable implementation of the recovered input-event pump.
- `resident_input.c`: target-side resident adapter for buffered/special input
  codes, key pressed edges, and framework event `0x1005`.
- `resident_keys.c`: direct target wrappers for key masks and
  down/pressed/released edge queries.
- `touch.c`: portable dispatcher for the verified four-word touch records.
- `resident_touch.c`: target-side touch queue pointer/count adapter.
- `resident_runtime.c`: target wrappers and loop for the resident
  setup/step/finalize lifecycle.
- `audio.c`: portable playback-state interpretation.
- `resident_audio.c`: target-side raw sound playback and state query.
- `resource_bundle.c`: portable word-pair and relative word-address helpers
  for authoring and inspecting linked bundles.
- `resource_graphics.c`: portable accessors for recovered bitmap and chunk
  dimensions.
- `settings_overlay.c`: portable setters for the verified family-B settings
  object mode, record, position, and visibility fields.
- `resident_resources.c`: target-side bundle registration and UI-family
  service wrappers.

No retail machine code or extracted proprietary assets belong in this tree.
