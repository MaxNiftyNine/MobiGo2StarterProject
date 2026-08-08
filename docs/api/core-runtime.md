# Core application and runtime API

## `resident_runtime.h`

`struct mg_sdk_runtime_callbacks` holds start, frame, and stop callbacks. The
resident owns frame scheduling and invokes them through its central step.

Primary operations:

- `mg_sdk_resident_runtime_setup()` initializes the resident title environment;
- `mg_sdk_resident_runtime_step()` advances one firmware-owned frame;
- `mg_sdk_resident_runtime_finalize()` releases title runtime state;
- `mg_sdk_resident_run()` performs the supported setup/step/finalize pattern.

The reserved scratch pointer passed to setup must be writable and remain valid
for setup. A zero result indicates failure. Applications should not continue
into resource registration after failed setup.

## Callback return contract

Start and frame return nonzero to continue. A frame returns zero when the
application intends to leave the resident loop, including after scheduling an
asynchronous MBA handoff. Stop runs during the normal finalization path.

Do not keep returning nonzero after `mg_sdk_resident_launch_mba()`. Do not spin
forever between finalize and the MBA-entry return.

## `application.h`

- `mg_sdk_resident_path_exists()` tests a resident application path.
- `mg_sdk_resident_launch_mba()` schedules another MBA with the resident launch
  service.

Paths are packed by the wrapper. Launch arguments are profile- and application-
specific; do not copy a numeric argument or regional filename from another slot.

## `memory_map.h`

This header defines a conservative maintained title-RAM range and default
starter reservations. They are 16-bit **word** addresses. The range is not a
general declaration that every byte is free under every firmware/application
combination.

Use immutable MBA storage for large const data and explicitly initialize every
writable arena. The range macros can detect overlapping static allocations in
project code.

## Startup skeleton

```c
static int start(void) { return initialize_owned_state(); }

static int frame(mg_sdk_u32 ticks)
{
    (void)ticks;
    mg_sdk_standard_controls_poll(&controls);
    update_game();
    render_game();
    return 1;
}

static void stop(void) { }
```

See [Lifecycle and memory](../guides/lifecycle-memory.md) for allocation and exit
rules.
