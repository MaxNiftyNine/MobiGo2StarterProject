# Buttons, keyboard, touch, and accelerometer

## Button and keyboard matrix

Physical buttons and keyboard keys share a six-row by nine-column GPIO matrix.
Software selects a row and reads active columns. The large D-pad and keyboard
arrow keys are different cells.

Resident applications should query logical game and system masks. Low-level
programs can use `hardware.h` to scan all rows and translate physical console
buttons. Raw scans require debouncing.

The canonical cells and emulator bindings are in the
[input matrix](../reference/input-matrix.md).

## Resistive touchscreen

The panel is a four-wire resistive touchscreen. Firmware uses GPIO contact
detection and manual ADC channels to measure axes, then publishes touch records
through the resident queue.

Resident coordinates are the supported application interface. Direct electrode
drive order, ADC calibration constants, and conversion timing are low-level
behavior and may vary from the emulator's calibrated model.

## Accelerometer

Firmware contains a Bosch-compatible path at I²C address `0x18`, bit-banged on
GPIO-E pins, plus evidence for an alternate Kionix-compatible device at `0x0f`.
The emulator implements chip detection, configuration storage, repeated-start
reads, and signed XYZ samples for the Bosch path.

Host arrows drive only the D-pad. Home, End, Page Up, and Page Down apply
deterministic left, right, up, and down tilt. These digital directions are
useful for automation but do not model the full analog motion profile of a
physical console.

## Input ownership

Do not scan GPIO rows while the resident is in the middle of its own scan.
Poll raw matrix input in a low-level loop that deliberately owns that hardware,
or use resident key state in a normal lifecycle application.
