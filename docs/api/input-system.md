# Input, touch, and system API

## Logical keys: `resident_keys.h`

The resident key wrappers return current masks or test a single mask as down,
pressed, or released. Game controls and dedicated system controls have separate
mask sets.

Use down/current for continuous movement and pressed/released for edges. The
resident updates these states as part of its frame pump.

## Input pump: `input.h` and `resident_input.h`

`input.h` implements host-testable translation of buffered and special input
events into a caller callback. `resident_input.h` binds that pump to the fixed
resident queue and framework event service.

Initialize a pump before polling it. Event callbacks must consume the provided
kind/code without retaining pointers into resident buffers.

## Touch: `touch.h` and `resident_touch.h`

The resident touch API exposes queue count and record pointers. The portable
touch parser converts records into contact state and coordinates.

Poll every frame and process release records. Do not assume a contact remains
down merely because the current queue is empty.

## Standard controls: `standard_controls.h`

```c
struct mg_sdk_standard_controls controls;

int mg_sdk_standard_controls_init(
    struct mg_sdk_standard_controls *controls,
    mg_sdk_u16 *bundle_ram);

void mg_sdk_standard_controls_poll(
    struct mg_sdk_standard_controls *controls);

void mg_sdk_standard_controls_hide(
    struct mg_sdk_standard_controls *controls);
```

`init` copies and registers the generated clean UI bundle, creates settings and
power-off objects, loads persisted volume/brightness, and applies them. It
returns 1 on success and 0 on failure. The caller retains the public struct but
must not mutate its internal policy, handles, or flags.

`poll` must run after the resident updates key edges. `hide` is safe after
successful initialization and clears active settings and power-off overlays.

## Direct-loop controls: `direct_controls.h`

```c
struct mg_sdk_direct_controls controls;

int mg_sdk_direct_controls_init(
    struct mg_sdk_direct_controls *controls);

void mg_sdk_direct_controls_poll(
    struct mg_sdk_direct_controls *controls);

void mg_sdk_direct_controls_hide(
    struct mg_sdk_direct_controls *controls);
```

This target-only adapter is for framebuffer loops that do not step resident UI.
It scans raw matrix edges but still delegates persistence, hardware setting
application, and power-off to resident services. It does not create or draw an
overlay. The public struct is caller-owned storage; do not mutate its policy,
matrix state, or edge fields.

Use `standard_controls.h` in a normal resident lifecycle application.

## Portable policy: `system_controls.h`

The lower-level policy accepts a complete backend of input, persistence,
hardware application, timing, presentation, feedback, and power operations.
It is suitable for host testing and custom integrations. New resident
applications should use the standard layer rather than rebuilding this backend.

See [Standard system controls](../guides/system-controls.md).
