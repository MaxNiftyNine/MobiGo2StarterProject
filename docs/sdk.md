# SDK guide

Include the complete public API with:

```c
#include "mobigo_sdk/mobigo_sdk.h"
```

## Application lifecycle

The firmware owns the outer runtime. A resident application performs setup,
registers copied resource graphs, creates its UI objects, and repeatedly calls
the runtime step with `start`, `frame`, and `stop` callbacks. `app/main.c` is the
canonical minimal implementation.

The MBA entry does not run an ordinary initialized-data C startup. Do not rely
on initialized mutable globals. Put large immutable tables, pixels, fonts, and
audio in `const` storage, then copy only mutable resource graphs into a chosen
title-RAM arena.

## Main API groups

| Header | Purpose |
| --- | --- |
| `application.h` | Portable callback runner and application state |
| `resident_runtime.h` | Setup, step, finalize, and resident timing |
| `input.h`, `resident_input.h` | Logical keys and physical matrix input |
| `resident_keys.h` | Edge-tested volume, brightness, and Off keys |
| `touch.h`, `resident_touch.h` | Raw and resident touch state |
| `system_controls.h` | Volume/brightness state and overlay model |
| `resident_resources.h` | Register and create firmware resource objects |
| `resource_bundle.h` | Parse and relocate version-2 resource bundles |
| `resource_graphics.h` | Family-A and Family-B graphics descriptors |
| `ui_family_b.h` | Sprites, UI objects, movement, and animation |
| `settings_overlay.h` | Standard volume/brightness/off object graph |
| `audio.h`, `resident_audio.h` | Playback and resident sound services |
| `audio_resources.h` | PCM8, ADPCM36, sequences, zones, and events |
| `resident_storage.h` | Config and file create/read/remove services |

The headers in `include/mobigo_sdk` are the API reference: each public type and
function has its calling and ownership contract beside the declaration.

## System controls

The starter registers the generated common UI and listens for
`MG_SDK_KEY_VOLUME_UP`, `MG_SDK_KEY_VOLUME_DOWN`,
`MG_SDK_KEY_BRIGHTNESS`, and `MG_SDK_KEY_OFF`. The overlay helpers mirror the
shared behavior found across retail titles, but all shipped art is newly
generated.

## Verification

`make test` exercises portable logic without firmware. `make target-check`
compiles the SDK with the u'nSP compiler. Focused emulator targets such as
`homebrew-check`, `storage-check`, `font-check`, and `audio-check` verify the
resident ABI against the included firmware image.
