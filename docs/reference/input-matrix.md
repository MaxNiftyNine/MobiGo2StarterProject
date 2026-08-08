# Input matrix and emulator bindings

The physical keyboard is a 6-row by 9-column switch matrix. Applications
normally consume resident logical-key masks; matrix cells are useful for
diagnostics and direct-framebuffer programs only.

## Host keyboard bindings

| Console input | Emulator key | Matrix cell |
| --- | --- | --- |
| Large D-pad Left/Right/Up/Down | Arrow keys | R3C3 / R4C3 / R3C4 / R4C4 |
| Primary action | Left or right Ctrl | R3C5 |
| Exit | Escape | R4C2 |
| Help | F1 | R4C5 |
| Off | F2 | R3C2 |
| Brightness | F6 | R4C6 |
| Volume Down / Up | F7 / F8 | R4C7 / R4C8 |
| Keyboard Left / Right | `[` / `]` | R3C0 / R4C0 |
| Enter | Return | R4C1 |
| Delete | Backspace | R2C5 |
| Space | Space | R3C1 |
| Question mark | `/` | R5C5 |
| Letter keys | matching host letter | rows 0–3 |
| Caps / Num | Caps Lock / Num Lock | R2C6 / R3C7 |
| Close emulator | F12 | not a matrix cell |

In both emulator modes the arrow keys drive only the large D-pad. Motion has
dedicated bindings: Home tilts left, End right, Page Up up, and Page Down down.
Fast mode changes host pacing, not the guest-visible input mapping.

## Complete matrix

| Row | C0 | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R0 | T | Y | U | I | O | P | W | E | R |
| R1 | F | G | H | J | K | L | A | S | D |
| R2 | C | V | B | N | M | Delete | Caps | Z | X |
| R3 | Key Left | Space | Off | D-pad Left | D-pad Up | Primary | Q | Num | unused |
| R4 | Key Right | Enter | Exit | D-pad Right | D-pad Down | Help | Brightness | Vol− | Vol+ |
| R5 | — | — | — | — | — | Question | — | — | — |

## Which API to use

- Resident applications: use `resident_keys.h` and call
  `mg_sdk_standard_controls_poll()` once per resident frame.
- Direct framebuffer loops: use `direct_controls.h` for system buttons, and
  the matrix helpers in `hardware.h` for game input when logical resident
  edges are unavailable.
- Host tests: inject logical events into the portable input/system-control
  policies instead of depending on a physical matrix.

Raw row values are active according to the target helper contract. Do not copy
MMIO addresses into application code; `hardware.h` centralizes the recovered
scan sequence and key translation.

**Evidence:** the cell map and host bindings are verified against the emulator
implementation and firmware input tables. Electrical details beyond the
public scan helper remain reverse-engineered rather than vendor-guaranteed.
