# MobiGo 2 input matrix

This is the current verified six-row by nine-column MobiGo 2 button and
keyboard matrix. `R` is the selected scan row and `C` is the returned column
bit. Software should debounce physical hardware input.

## Hardware buttons

| Control | Matrix cell |
|---|---|
| Up | R3 C4 |
| Down | R4 C4 |
| Left | R3 C3 |
| Right | R4 C3 |
| Off | R3 C2 |
| Exit | R4 C2 |
| Help | R4 C5 |
| Primary | R3 C5 |
| Volume down | R4 C7 |
| Volume up | R4 C8 |
| Brightness | R4 C6 |

## Keyboard

| Key | Matrix cell | Key | Matrix cell | Key | Matrix cell |
|---|---|---|---|---|---|
| Q | R3 C6 | W | R0 C6 | E | R0 C7 |
| R | R0 C8 | T | R0 C0 | Y | R0 C1 |
| U | R0 C2 | I | R0 C3 | O | R0 C4 |
| P | R0 C5 | A | R1 C6 | S | R1 C7 |
| D | R1 C8 | F | R1 C0 | G | R1 C1 |
| H | R1 C2 | J | R1 C3 | K | R1 C4 |
| L | R1 C5 | Z | R2 C7 | X | R2 C8 |
| C | R2 C0 | V | R2 C1 | B | R2 C2 |
| N | R2 C3 | M | R2 C4 | Caps | R2 C6 |
| Num | R3 C7 | Question mark | R5 C5 | Space | R3 C1 |
| Keyboard left arrow | R3 C0 | Keyboard right arrow | R4 C0 | Enter | R4 C1 |
| Delete | R2 C5 |  |  |  |  |

The keyboard arrow keys above are keys on the MobiGo keyboard and are distinct
from the four large directional controls.

## Emulator host bindings

The included emulator delivers ordinary letter keys to their matching MobiGo
keyboard cells. Additional host bindings are:

| Host key | MobiGo control |
|---|---|
| Arrow keys | Large D-pad and matching accelerometer tilt |
| Left or right Control | Primary |
| Escape | Exit |
| F1 | Help |
| F2 | Off |
| F6 | Brightness |
| F7 / F8 | Volume down / up |
| Caps Lock / Num Lock | Caps / Num |
| `/` | Question mark |
| `[` / `]` | Keyboard left / right arrow |
| Return | Keyboard Enter |
| Backspace | Delete |
| F12 | Close emulator |

Scripted emulator input uses the same logical names with
`--key-event at,duration,key`. Examples:

```sh
--key-event 800000000,5000000,primary
--key-event 850000000,30000000,right
--key-event 900000000,5000000,space
```

The `left`, `right`, `up`, and `down` scripted names also drive both input
paths. This duplication is intentional: games that read the D-pad keep working,
while games that use the MobiGo 2 motion sensor receive a digital one-g tilt.
