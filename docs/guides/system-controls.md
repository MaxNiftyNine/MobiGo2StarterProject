# Standard volume, brightness, and Off behavior

MobiGo 2 applications are expected to preserve the console's dedicated system
controls. New applications should use the target-only convenience layer in
`mobigo_sdk/standard_controls.h`.

## Canonical near-automatic integration

The standard layer owns the portable policy, generated clean-room UI resources,
resident UI handles, and readiness state. The application supplies writable
title RAM for the mutable generated bundle.

```c
#include "mobigo_sdk/standard_controls.h"

static struct mg_sdk_standard_controls controls;

/* writable_bundle points to application-owned title RAM */
if (!mg_sdk_standard_controls_init(&controls, writable_bundle)) {
    /* fail safely: the standard resources could not be registered */
}
```

Poll once per resident frame:

```c
mg_sdk_standard_controls_poll(&controls);
```

Hide any transient presentation when a scene or application explicitly needs
to clear it:

```c
mg_sdk_standard_controls_hide(&controls);
```

## What the standard layer handles

- pressed-edge detection for Volume Up, Volume Down, Brightness, and Off;
- ten logical volume levels and four brightness levels;
- loading, applying, and persisting current settings through resident services;
- generated clean-room volume and brightness overlays with timeout behavior;
- maximum-volume visual/policy handling (no claimed feedback sound);
- generated Off object submission followed by the resident power request;
- resident resource registration and UI object creation.

Initialization can fail if writable storage is invalid or resident resources
cannot be created. Treat that as a startup error rather than silently dropping
system behavior.

## Writable bundle memory

The generated resource graph is mutable after registration. Pass a suitably
sized, aligned region of application-owned title RAM. Do not point it at `const`
MBA data, stack memory, framebuffer memory, or resident-owned low RAM.

The generated header documents the exact storage requirement. Keep game state
and other resource graphs outside that range.

## Game mappings and system buttons

Dedicated system buttons should keep their system behavior even when a game
also treats one as an action. Poll the standard layer first, then read the
logical edge for the game if that dual use is intentional and documented.

Help is normally a game/application control rather than a system setting.
Brightness is a system control. Prefer Help as an extra action before assigning
Brightness alone.

## Lower-level policy API

`mobigo_sdk/system_controls.h` remains the portable policy engine. It accepts a
backend containing input, persistence, hardware-application, timing,
presentation, feedback, and power callbacks.

Use it when:

- testing the policy on a host;
- providing a non-resident backend;
- replacing the standard presentation with original project-specific UI;
- integrating with a deliberately low-level runtime.

Using the low-level policy means the application owns every backend operation.
Drawing an overlay without applying and saving the setting is incomplete.

## Direct framebuffer loops

A loop that takes framebuffer ownership and does not step the resident
lifecycle cannot render resident overlays. Use the target-only direct layer:

```c
#include "mobigo_sdk/direct_controls.h"

static struct mg_sdk_direct_controls controls;

if (!mg_sdk_direct_controls_init(&controls)) {
    /* caller-owned control storage was invalid */
}

/* once per owned frame */
mg_sdk_direct_controls_poll(&controls);
```

`direct_controls.h` scans the 6×9 matrix, detects system-button edges, and uses
resident services to load/save levels, apply volume/brightness, and request
power-off. It intentionally draws no volume, brightness, or Off overlay because
resident rendering is not active. `mg_sdk_direct_controls_hide()` clears the
portable presentation state but cannot hide a resident object that was never
created.

Prefer `standard_controls.h` whenever the application uses the resident frame
pump. The direct layer is a compatibility path for software-renderer loops, not
a faster version of the standard layer.

## Testing

For each application, verify:

1. both volume directions clamp correctly;
2. brightness cycles through all four levels;
3. standard-layer overlays appear and expire without blocking the game, or a
   direct-loop application clearly documents that overlays are unavailable;
4. repeated holds do not produce uncontrolled edges;
5. settings survive the supported persistence path;
6. Off reaches the terminal power request; for the standard layer verify object
   submission precedes the request, without assuming a frame is displayed;
7. game mappings sharing Help or Brightness still preserve the intended system
   behavior.

Use emulator F-key bindings from the [input matrix](../reference/input-matrix.md)
and include these checks in the application smoke test.
