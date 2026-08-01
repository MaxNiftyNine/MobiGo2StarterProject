# UI-object and touchscreen runtime

This note records the G1 evidence for the resident UI and touchscreen
services. Names are clean-room working names unless stated otherwise.

## Resident UI-object families

The fixed service bank contains at least two related object families:

| Service | Implementation | Observed role |
|---:|---:|---|
| `0x075f06` | `0x056a68` | Create family-A graphics/resource object |
| `0x075f08` | `0x056a90` | Destroy family-A object |
| `0x075f0e` | `0x056be3` | Get family-A object storage |
| `0x075f12` | `0x056c54` | Create family-B UI object |
| `0x075f14` | `0x056ca4` | Destroy family-B UI object |
| `0x075f18` | `0x056e7c` | Get family-B object storage |
| `0x075f1c` | `0x056ffe` | Bind an event/callback according to object type |
| `0x075f28` | `0x069181` | Create a nine-field scheduled/event record |
| `0x075f2a` | `0x069210` | Destroy that scheduled/event record |

G1 uses family B for the common setting overlays: object type `0x0e` for
volume/brightness and type `0x30` for the power-off presentation. The object
storage is then filled with positions, modes, levels, and resource-specific
fields. The exact generic layouts remain provisional; the clean-room SDK
currently presents the proven policy through backend callbacks instead of
freezing an incorrect binary object structure.

## Resident touchscreen queue

Two resident services expose a per-frame touchscreen queue:

| Service | Implementation | Behavior |
|---:|---:|---|
| `0x075f3a` | `0x06cbd1` | Returns a far pointer to the first queue record |
| `0x075f3c` | `0x06cbda` | Returns the queue record count |

The pointer returned by `0x075f3a` is the resident touch-state allocation plus
one word. The count is stored at allocation offset `0x03fe`.

The neighboring services form the rest of the touchscreen subsystem:

| Service | Implementation | Observed role |
|---:|---:|---|
| `0x075f30` | `0x06ca68` | Initialize touch state with two far-pointer arguments |
| `0x075f32` | `0x06caa5` | Shut down/reset touch state |
| `0x075f34` | `0x06cade` | Poll hardware and build the current queue |
| `0x075f36` | `0x06cbba` | Return the current enable/state word |
| `0x075f38` | `0x06cbc3` | Clear records, then set the enable/state word |
| `0x075f3e` | `0x06cbe6` | Clear fifteen four-word working records |
| `0x075f40` | `0x06cc1c` | Register an event handler by event nibble/owner |
| `0x075f42` | `0x06ccd5` | Remove a matching event handler |
| `0x075f44` | `0x06ccf6` | Reset touch handler and record state |

Resident runtime step `0x075f48` calls `0x06cade` every frame before
application code runs. Homebrew using that standard lifecycle should consume
the queue but should not call the low-level update a second time.

G1's dispatcher at `0x0df8fa` (annotated
`sdk_dispatch_touch_events` in Ghidra) proves that each record is four
16-bit words:

```text
word 0: signed x coordinate
word 1: signed y coordinate
word 2: not consumed by G1's dispatcher
word 3: not consumed by G1's dispatcher
```

It visits every queued record. If either coordinate is `-1`, it supplies
state `2`; otherwise it supplies state `0`. It saves the latest x, y, and
state in local runtime globals and invokes the registered callback as:

```c
callback(registered_object, x, y, derived_state, 0);
```

The callback's object/owner handle is represented by two 16-bit words in the
u'nSP ABI. The semantic names of state 0 and state 2 are not yet proven, so
the clean-room API calls them `COORDINATE` and `SENTINEL` rather than assuming
press/move/release.

The combined high-level input poller at `0x0dfb86`, annotated
`sdk_poll_high_level_input`, first runs game-control edge dispatch, buffered
keyboard translation, and another input translator, then dispatches the
touch queue.

## Clean-room API

`touch.h` provides a portable counted-queue adapter. It preserves the two
unknown record words so later cross-title comparison cannot silently discard
information. `resident_touch.h` binds that adapter to services `0x075f3a`
and `0x075f3c`.

No retail graphics, sound, or object data is copied into the implementation.
The UI backend is intentionally semantic until another title confirms the
generic family-A/family-B object layouts.
