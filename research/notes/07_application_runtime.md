# Resident application lifecycle and frame pump

The captured resident implementation establishes the contract behind the
three fixed services called by G1's MBA entry point:

| Service | Implementation | Effective operation |
|---:|---:|---|
| `0x075f46` | `0x06bc99` | Initialize the resident application runtime |
| `0x075f48` | `0x06bd04` | Select an app descriptor and run one frame |
| `0x075f4a` | `0x06bf07` | Shut down the resident application runtime |

Names are clean-room descriptions, not recovered official symbols.

## Six-word callback descriptor

`0x075f48` takes one 32-bit far pointer to a descriptor containing three
32-bit far function pointers:

```c
struct resident_app_callbacks {
    int  (*start)(void);              /* words 0..1 */
    int  (*frame)(unsigned long now); /* words 2..3 */
    void (*stop)(void);               /* words 4..5 */
};
```

This is exactly six 16-bit words with the Generalplus compiler's
32-bit pointer model. G1 passes a descriptor at data-space word address
`0x5d1c`. Its identified application callbacks are consistent with:

- `sdk_runtime_init` at `0x0e0000`: startup, returns 1;
- `sdk_runtime_tick_and_handoff` at `0x0e0075`: per-frame work, returns 1 to
  continue or 0 after scheduling an MBA handoff;
- the stop callback is not yet identified and may be null in G1.

## Descriptor switching

The resident step function stores the currently selected descriptor. When a
different pointer is supplied, it:

1. invokes the prior descriptor's stop callback when present;
2. stores the new descriptor;
3. invokes its start callback when present;
4. aborts the selection if start returns zero.

After resident processing it invokes `frame(now)` when present. A zero return
ends the application and invokes stop when present. A nonzero return keeps
the frame loop active.

## Firmware-owned frame ordering

Before calling the app's frame callback, `0x075f48` obtains the 32-bit tick
count and updates the resident subsystems in a fixed order. Proven members of
that sequence include:

1. system-key state (`0x0657c7`);
2. timer/event facilities;
3. audio;
4. game-control state (`0x06d397`);
5. touchscreen queue (`0x06cade`);
6. buffered input and additional device/event facilities.

It then applies device-state policy, invokes the app frame callback, and
finishes resident presentation/scheduling work. This explains why official
games can query pressed/released edges and a complete touch queue without
manually polling hardware.

`0x075f46` initializes the same resident subsystem set, including both key
state machines and touch. `0x075f4a` shuts them down in reverse-style order.
G1 passes a reserved two-word scratch pointer to setup; the captured firmware
does not consume its contents.

## Clean-room interface

`resident_runtime.h` exposes the callback descriptor, raw setup/step/finalize
wrappers, and `mg_sdk_resident_run()` for the standard loop. The target
compiler successfully builds the descriptor and fixed-address calls.

The normal MBA entry still has launcher-specific argument decoding before
this loop. That bootstrap structure is separate from the callback contract
and remains under analysis.
