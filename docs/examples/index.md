# Examples and probes

Examples demonstrate a specific API or hardware route. They are not all starter
templates, and their target profile is part of what they demonstrate.

## Recommended reading order

1. `app/main.c`: canonical new SY application and resident lifecycle.
2. `examples/runtime_poll.c`: focused resident input/system polling.
3. `examples/resident_lifecycle.c`: callback contract.
4. Generated UI, font, animation, audio, and storage probes selected by the
   related Make targets.
5. Complete projects only after reading their target banner and build script.

## Focused probes

| Area | Source or target |
| --- | --- |
| Lifecycle | `runtime_poll.c`, `resident_lifecycle.c` |
| System presentation | `system_ui_generated_boot_demo.c` |
| Graphics | Family-A and Family-B generated boot demos |
| Text | dynamic font baseline and boot demo |
| Effects | PCM8, S sequence, and ADPCM36 probes |
| Music | multizone, ADPCM36, and auxiliary M probes |
| Storage | existing-file/read/write/remove probes on copied NAND |

Generated probes keep immutable payloads `const` and copy mutable graphs into
title RAM before registration.

## Hardware suite

`examples/hardware_test_suite/` is an SY-only guided diagnostic, not a game
starter. See the [hardware-suite guide](../testing/hardware-suite.md).

## Complete projects

Color Cycle is the maintained low-level SY example. The monochrome movie player
and MobiGo Celeste are explicit legacy G1 examples. Their renderer and asset
techniques remain useful, but new ports must not inherit G1 merely by copying
them.

[Homebrew Launcher](homebrew-launcher.md) is the maintained SY menu example. It
demonstrates dynamic text, standard controls, animated light-blue waves,
validated catalog loading, and asynchronous launch of `.MBA` files below
`/HB`.

See [Complete projects](complete-projects.md).
