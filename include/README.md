# Reconstructed headers

Public clean-room API declarations:

- `mobigo_sdk/mobigo_sdk.h`: umbrella include for the current reconstructed
  SDK.
- `mobigo_sdk/system_controls.h`: portable volume, brightness, transient
  overlay, and power-off policy reconstructed from the shared runtime.
- `mobigo_sdk/resident_addresses.h`: centralized fixed word addresses for
  strongly supported resident services; intentionally does not guess
  unresolved prototypes.
- `mobigo_sdk/resident_backend.h`: experimental target-only adapter for the
  fixed resident service bank.
- `mobigo_sdk/application.h`: recovered target-side path testing and
  asynchronous MBA launch request.
- `mobigo_sdk/input.h`: host-testable common keyboard/game-control event-pump
  policy using raw verified masks.
- `mobigo_sdk/resident_input.h`: experimental target adapter for the fixed
  resident input and event-posting services.
- `mobigo_sdk/resident_keys.h`: direct current/down/pressed/released queries
  for the resident system-key and game-control state machines.
- `mobigo_sdk/touch.h`: portable four-word touchscreen queue adapter.
- `mobigo_sdk/resident_touch.h`: target binding for the resident touchscreen
  queue pointer and count services.
- `mobigo_sdk/resident_runtime.h`: recovered three-callback application
  lifecycle and the firmware-owned central frame pump.
- `mobigo_sdk/audio.h`: verified resident playback-state interpretation.
- `mobigo_sdk/resident_audio.h`: experimental raw playback and state-query
  facade using 32-bit resource and sound handles.
- `mobigo_sdk/resource_bundle.h`: partially recovered `0x20`-word linked
  asset-bundle header, UI descriptor sizes, standard settings records, and
  word-address helpers.
- `mobigo_sdk/resource_graphics.h`: recovered component-list, six-word bitmap,
  and four-word bitmap-chunk layouts.
- `mobigo_sdk/settings_overlay.h`: verified family-B mutable fields for
  selecting, positioning, showing, and hiding a settings record.
- `mobigo_sdk/resident_resources.h`: target wrappers for registering a linked
  bundle and creating/destroying/accessing both resident UI families.

Platform adapters provide hardware and presentation operations. This keeps the
recovered behavior reusable while requiring original homebrew graphics and
sounds.
