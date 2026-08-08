# Runtime, input, and controls callables

## `application.h` — target-only handoff

```c
int mg_sdk_launch_pack_path(
    mg_sdk_u16 *destination,
    const char *source);

int mg_sdk_resident_path_exists(const char *path);

void mg_sdk_resident_launch_mba(
    const char *path,
    mg_sdk_u16 argument_count,
    const mg_sdk_u32 *arguments);
```

`mg_sdk_launch_pack_path()` packs a launch path into caller-provided storage of
at least `MG_SDK_LAUNCH_PATH_WORDS` words. It returns one on success and zero
for null pointers or a path longer than `MG_SDK_LAUNCH_PATH_MAX_CHARS`; it does
not silently truncate. `mg_sdk_resident_path_exists()` uses the resident
filesystem predicate. `mg_sdk_resident_launch_mba()` schedules an asynchronous
handoff; it does not jump. It accepts the same bounded launch path and copies at
most `MG_SDK_LAUNCH_MAX_ARGUMENTS` 32-bit arguments. After scheduling from a
frame callback, return zero, finalize the runtime, and return from MBA entry.
Argument meaning and target path are application/firmware specific.

**Ownership/evidence:** the packing destination belongs to the caller; the
launcher copies path and argument data during the call. Target-only;
scheduling/finalization is emulator-verified and physically observed for the
bounded fixtures in the capability matrix.

## `resident_runtime.h` — target-only lifecycle

```c
int mg_sdk_resident_runtime_setup(mg_sdk_u32 *reserved_scratch);

int mg_sdk_resident_runtime_step(
    const struct mg_sdk_runtime_callbacks *callbacks);

void mg_sdk_resident_runtime_finalize(void);

int mg_sdk_resident_run(
    const struct mg_sdk_runtime_callbacks *callbacks);
```

`mg_sdk_resident_runtime_setup()` returns zero on failure and accepts writable
two-word scratch. `mg_sdk_resident_runtime_step()` invokes the registered
start/frame contract and returns whether execution should continue.
`mg_sdk_resident_runtime_finalize()` closes the resident title lifecycle.
`mg_sdk_resident_run()` performs the complete pattern, returning zero only when
setup fails and one after orderly finalization.

The callback struct is caller-owned and must remain valid through every step.
Its start/frame callbacks return nonzero to continue; stop returns void.
Target-only; callback layout is target-compiled and exercised through firmware
integration.

## `input.h` and `resident_input.h`

```c
void mg_sdk_input_init(
    struct mg_sdk_input_pump *pump,
    const struct mg_sdk_input_backend *backend,
    void *user);

void mg_sdk_input_poll(struct mg_sdk_input_pump *pump);
```

`mg_sdk_input_init()` binds caller-owned pump storage to a backend and user
context. `mg_sdk_input_poll()` consumes the first buffered keyboard code,
special-code latches, game pressed edges, and the Off system pressed edge, then
calls the backend's event sink with `MG_SDK_INPUT_KEYBOARD`,
`MG_SDK_INPUT_GAME_CONTROL`, or `MG_SDK_INPUT_SYSTEM_KEY`.

The backend and user context must outlive the pump. The event pointer supplied
to `post_event` is valid only during that callback. Policy is host-tested;
`mg_sdk_experimental_resident_input_backend` is the target adapter exported by
`resident_input.h` and retains the stated experimental evidence label.

## `resident_keys.h` — target logical state

```c
mg_sdk_u16 mg_sdk_resident_system_keys(void);
int mg_sdk_resident_system_key_down(mg_sdk_u16 mask);
int mg_sdk_resident_system_key_pressed(mg_sdk_u16 mask);
int mg_sdk_resident_system_key_released(mg_sdk_u16 mask);

mg_sdk_u16 mg_sdk_resident_game_keys(void);
int mg_sdk_resident_game_key_down(mg_sdk_u16 mask);
int mg_sdk_resident_game_key_pressed(mg_sdk_u16 mask);
int mg_sdk_resident_game_key_released(mg_sdk_u16 mask);
```

The two `*_keys()` calls return the current mask. `*_key_down()` tests current
level; `*_key_pressed()` and `*_key_released()` test resident-maintained edges
and return C truth values. Query after the resident frame pump has updated input.
Masks come from `enum mg_sdk_system_key` and `enum mg_sdk_game_key_mask`.

No returned storage is owned by the caller. Target-only; matrix-to-logical
mapping and resident edges have emulator integration coverage and bounded
physical evidence.

## `touch.h` and `resident_touch.h`

```c
void mg_sdk_touch_poll(
    const struct mg_sdk_touch_backend *backend,
    void *backend_user,
    mg_sdk_touch_callback callback,
    void *callback_user);

const mg_sdk_u16 *mg_sdk_resident_touch_event_words(void);
mg_sdk_u16 mg_sdk_resident_touch_event_count(void);
```

`mg_sdk_touch_poll()` parses each four-word backend record and invokes the
callback with signed coordinates, coordinate/sentinel state, and preserved raw
tail words. The event pointer is callback-scoped. The backend and callback must
be non-null and remain valid for the poll.

`mg_sdk_resident_touch_event_words()` returns resident-owned queue storage;
consume it in the current frame and do not retain or modify it.
`mg_sdk_resident_touch_event_count()` returns the current record count.
`mg_sdk_experimental_resident_touch_backend` combines both for the portable
poller. Parsing is host-tested; target queue use is emulator-verified with
limited physical calibration coverage.

## `system_controls.h` — portable policy

```c
void mg_sdk_system_controls_init(
    struct mg_sdk_system_controls *controls,
    const struct mg_sdk_system_backend *backend,
    void *user);

void mg_sdk_system_controls_poll(
    struct mg_sdk_system_controls *controls);

void mg_sdk_system_controls_hide(
    struct mg_sdk_system_controls *controls);

void mg_sdk_volume_set(
    struct mg_sdk_system_controls *controls,
    mg_sdk_u16 level,
    int show_overlay);

void mg_sdk_brightness_set(
    struct mg_sdk_system_controls *controls,
    mg_sdk_u16 level,
    int show_overlay);
```

`mg_sdk_system_controls_init()` loads valid persisted levels (or defaults),
applies their gain/backlight table values, and initializes timeout/power state.
`mg_sdk_system_controls_poll()` handles pressed edges, level bounds,
persistence, presentation timeout, and terminal Off policy.
`mg_sdk_system_controls_hide()` clears current presentation.
`mg_sdk_volume_set()` clamps to the highest volume level, then saves, applies,
and optionally presents it. `mg_sdk_brightness_set()` wraps modulo the four
brightness levels before performing the same operations.

Controls storage, backend function table, and user context are caller-owned and
must remain valid. Missing optional callbacks suppress only their operation;
the policy returns void. This layer is host-tested. A custom backend owns every
input, persistence, hardware, timing, presentation, feedback, and power action.

## `standard_controls.h` — resident lifecycle convenience

```c
int mg_sdk_standard_controls_init(
    struct mg_sdk_standard_controls *controls,
    mg_sdk_u16 *bundle_ram);

void mg_sdk_standard_controls_poll(
    struct mg_sdk_standard_controls *controls);

void mg_sdk_standard_controls_hide(
    struct mg_sdk_standard_controls *controls);
```

`mg_sdk_standard_controls_init()` returns one after copying/registering the
clean UI bundle, creating settings/Off handles, loading persisted levels, and
applying them; it returns zero for invalid storage or UI creation failure.
`bundle_ram` is caller-owned writable title RAM retained as the registered graph.
`mg_sdk_standard_controls_poll()` runs once after each resident input update.
`mg_sdk_standard_controls_hide()` hides settings and Off objects after a
successful init.

The Off edge submits the clean Off object and then requests resident power-off
in the same poll. Ordering is tested, but a displayed frame is not guaranteed
because callbacks stop at the terminal request. There is no claimed retail or
generated feedback sound; maximum-level behavior is visual/policy only.
Target-only; policy, generated-resource, emulator, and bounded hardware evidence
are tracked separately.

## `direct_controls.h` — framebuffer-owned loop

```c
int mg_sdk_direct_controls_init(struct mg_sdk_direct_controls *controls);
void mg_sdk_direct_controls_poll(struct mg_sdk_direct_controls *controls);
void mg_sdk_direct_controls_hide(struct mg_sdk_direct_controls *controls);
```

`mg_sdk_direct_controls_init()` initializes caller-owned state and seeds current
raw system keys, returning zero only for a null controls pointer.
`mg_sdk_direct_controls_poll()` scans the matrix, derives pressed edges, runs
portable policy through resident persistence/apply/power operations, clears the
temporary edge mask, and services the watchdog.
`mg_sdk_direct_controls_hide()` clears policy presentation state.

No function draws an overlay: resident UI is not being stepped. The struct is
public only so the caller can allocate it; do not mutate its policy, matrix, or
edge fields. Target-only; use `standard_controls.h` whenever resident rendering
is active.
