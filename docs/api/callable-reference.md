# Complete callable reference

This index covers every public callable declared under `include/mobigo_sdk/`.
It is organized by ownership and runtime layer; each linked page gives exact C
signatures, return conventions, storage lifetime, and evidence boundaries.

| Reference | Headers covered |
| --- | --- |
| [Runtime, input, and controls](callables-runtime-input.md) | `application.h`, `resident_runtime.h`, `input.h`, `resident_input.h`, `resident_keys.h`, `touch.h`, `resident_touch.h`, `system_controls.h`, `standard_controls.h`, `direct_controls.h` |
| [Graphics and resources](callables-graphics.md) | `resource_bundle.h`, `resource_graphics.h`, `ui_family_b.h`, `settings_overlay.h`, `resident_resources.h` |
| [Audio and storage](callables-audio-storage.md) | `audio.h`, `audio_resources.h`, `resident_audio.h`, `resident_storage.h` |
| [Low-level hardware](hardware.md) | `hardware.h`, with memory constants from `memory_map.h` |

The remaining public headers are declaration/configuration surfaces rather than
callable families:

- `mobigo_sdk.h` is the umbrella include;
- `resident_addresses.h` centralizes supported resident word addresses;
- `resident_backend.h` exports the target backend object used by controls;
- `memory_map.h` defines title-RAM ranges and overlap macros.

## Target language and ABI

Application code is C. The bundled target builder accepts C99-style `.c` and
u'nSP assembly `.asm`/`.s` sources. It does not provide a target C++ frontend,
and the public API does not establish a C++ ABI. Emulator2 is a separate host
program written in C++20; that does not make C++ a supported MBA language.

All signatures below are clean-room API contracts, not recovered vendor symbol
names. Word-addressed pointers, target-only calls, resident handles, and
host-portable authoring helpers are labeled separately.
