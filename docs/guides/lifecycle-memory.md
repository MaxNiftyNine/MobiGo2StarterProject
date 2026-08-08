# Application lifecycle and memory

MobiGo 2 firmware owns the outer runtime. A homebrew MBA joins that environment,
registers resources, runs callbacks through the resident frame pump, and
finalizes before an intentional handoff or exit.

## Callback model

The public runtime uses three callbacks:

- start: initialize application state and return nonzero to continue;
- frame: process one resident frame and return nonzero while active;
- stop: release application-owned state before finalization.

`mg_sdk_resident_run()` is the highest-level runner. The setup, step, and
finalize functions are available when an application needs explicit control.

The resident may update input, touch, UI, audio, clocks, and pending application
handoffs around the callback. Do not replace the frame callback with an
unbounded desktop-style main loop.

## No conventional C startup

The generated MBA entry jumps into application code without a normal reset-time
CRT pass. In particular, do not assume:

- writable initialized data was copied from ROM;
- BSS was cleared;
- low internal RAM belongs to the application;
- constructors or platform runtime hooks executed.

Safe patterns are:

```c
static const struct game_state initial_state = {
    /* immutable template */
};

/* During start, copy initial_state into application-owned writable RAM. */
```

or explicit assignment of every field before its first read.

## Memory categories

| Memory | Typical use | Rule |
| --- | --- | --- |
| executable/const payload | code, pixels, waveforms, lookup tables | keep immutable |
| title RAM | game state and relocated resource graphs | choose and initialize explicitly |
| inherited framebuffer | final display surface | query; never assume an address |
| resident-owned memory | firmware services and objects | access only through the API |
| stack | bounded temporary state | avoid large automatic arrays and deep recursion |

Resource bundles contain pointers that the resident rebases in place. Copy the
mutable graph into writable title RAM before registration; immutable primary
pixel or waveform storage can remain in the MBA.

## Exiting and relaunching

Application launch requests are asynchronous. Scheduling another MBA is not the
same as jumping to it immediately. The frame callback must return zero, the
resident runtime must finalize, and the MBA entry must return according to the
profile's contract.

Continuing to return nonzero after scheduling leaves the handoff pending. A
permanent spin after finalization prevents it as well.

## Low-level loops

When a port intentionally owns a low-level loop:

- preserve inherited interrupt state;
- kick the watchdog frequently;
- query the live framebuffer;
- keep input and system behavior progressing;
- yield or segment long conversion work at predictable points.

Use `hardware.h` rather than duplicating register addresses. Prefer the resident
lifecycle unless the port has a measured reason not to.

## Review checklist

Search a new port for writable globals with initializers, static local state,
large stack arrays, direct framebuffer constants, infinite loops, direct system
button mappings, and exit paths that bypass finalization.
