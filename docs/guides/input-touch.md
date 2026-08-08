# Input, keyboard, touch, and motion

Use logical resident input for normal applications. Raw matrix access is for a
deliberately low-level frame loop or hardware diagnosis.

## Logical game controls

The main logical controls are Up, Down, Left, Right, Primary, Exit, and Help.
The resident API exposes current, down, pressed-edge, and released-edge queries.

Choose semantics deliberately:

- current/down is appropriate for continuous movement;
- pressed edge is appropriate for jump, menu confirmation, or pause;
- released edge is useful for gestures and key-repeat state machines.

Do not implement edge detection from an occasional raw sample if the resident
already supplies it.

## Keyboard alternatives

The built-in keyboard is part of the same electrical matrix but has distinct
cells from the large D-pad and Primary button. A game can support both physical
controls and letter-key alternatives.

Document every mapping in the project README and deterministic emulator test.
Test the physical and keyboard alternatives independently; one working host key
does not prove both matrix cells.

## Touch records

The resident touchscreen queue provides four-word records and a release
sentinel. The portable touch helper converts queue records into down, move, and
up state. Consume all queued records each frame so a short contact is not lost.

Touch coordinates should be treated as screen coordinates after the resident
calibration path. Direct ADC calibration belongs to low-level hardware work and
must not be substituted into a resident application casually.

## Motion sensor

The MobiGo 2 contains a three-axis accelerometer on a bit-banged I²C bus. The
emulator models the verified Bosch-compatible path and digital tilt. Arrows
drive the large D-pad only. Home, End, Page Up, and Page Down provide left,
right, up, and down motion without closing D-pad matrix switches.

Applications using motion should include a neutral range, orientation note, and
calibration/dead-zone policy. Digital host tilt is useful for deterministic
tests but does not represent analog physical movement.

## Raw matrix access

`hardware.h` exposes row initialization and scan helpers for target-only use.
Raw scans must select a valid row, interpret active levels correctly, and
debounce physical input. Prefer the resident logical API when firmware owns the
frame lifecycle.

The complete verified cells and host bindings are in the
[input matrix](../reference/input-matrix.md).

## Test matrix

For each consumed action, test:

- press, hold, and release;
- physical control and keyboard alternative;
- two simultaneous directions where the game permits them;
- focus loss or emulator reset clearing stuck state;
- touch down/move/up order;
- neutral and directional motion values if used.
