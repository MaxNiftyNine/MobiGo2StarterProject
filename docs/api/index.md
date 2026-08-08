# Public API overview

Include the complete supported surface with:

```c
#include "mobigo_sdk/mobigo_sdk.h"
```

For a library or focused probe, including the narrow header makes dependencies
and target requirements clearer.

Every public function is searchable with its exact signature, return behavior,
ownership, and evidence boundary in the
[complete callable reference](callable-reference.md). The focused pages below
explain design and common integration patterns.

## API groups

| Group | Headers | Availability |
| --- | --- | --- |
| Lifecycle | `application.h`, `resident_runtime.h` | target resident firmware |
| Standard console behavior | `standard_controls.h` | target resident firmware |
| System controls in an owned framebuffer loop | `direct_controls.h` | target resident services plus raw matrix |
| Portable system policy | `system_controls.h` | host and target |
| Input and touch | `input.h`, `touch.h`, `resident_input.h`, `resident_keys.h`, `resident_touch.h` | mixed portable/target |
| Graphics and UI | `resource_bundle.h`, `resource_graphics.h`, `ui_family_b.h`, `settings_overlay.h`, `resident_resources.h` | authoring portable; resident operations target-only |
| Audio | `audio.h`, `audio_resources.h`, `resident_audio.h` | authoring portable; playback target-only |
| Storage | `resident_storage.h` | target resident firmware |
| Low-level hardware | `hardware.h`, `memory_map.h` | target-only |
| Resident internals | `resident_addresses.h`, `resident_backend.h` | advanced target integration |

## Common types

The SDK uses fixed-width aliases suitable for the Generalplus compiler:

- `mg_sdk_u16` and `mg_sdk_s16` for 16-bit values;
- `mg_sdk_u32` for 32-bit values and far word addresses;
- 32-bit handles for resident UI and audio objects.

Hardware and linker addresses are normally **word addresses**. File sizes,
ordinary host paths, and encoded file offsets remain bytes unless explicitly
labeled otherwise.

## Ownership vocabulary

- **Caller-owned** memory must remain valid for the stated operation or object
  lifetime.
- **Resident-owned** objects are accessed through handles and must not be
  dereferenced as application pointers.
- **Relocated in place** means registration mutates tagged pointers in the
  supplied writable graph.
- **Target-only** means the function calls firmware or hardware addresses and
  must not execute in a host test process.

## Stability and evidence

Public names are clean-room descriptions, not claims about vendor symbol names.
Resident wrappers are supported when they have a known calling contract and a
repeatable emulator test. Physical evidence is tracked separately in the
[capability matrix](../testing/capability-matrix.md).

Avoid calling a raw address from `resident_addresses.h` when a typed wrapper
exists. An address constant does not by itself establish a prototype.
