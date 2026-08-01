# MobiGo 2 motion sensor

Status: the electrical interface, device-detection paths, sample format, and
resident conversion routine are confirmed from retail code. The physical
orientation signs are confirmed from the conversion routine and the neutral
gravity sample. The emulator implements the BMA222E path used by the captured
runtime.

## Result

The feature games call "motion" or "tilt" is a three-axis accelerometer, not a
rate gyroscope. The resident firmware hides two supported chip families behind
one signed XYZ interface:

| Path | 7-bit I2C address | Identification | Sample registers |
|---|---:|---|---|
| Bosch BMA222E | `0x18` | register `0x00` = `0xF8` | six bytes from `0x02` |
| Kionix-compatible | `0x0F` | register `0x0F` = `0x07` or `0x0A` | six bytes from `0x06` |

The GPL16250 firmware bit-bangs I2C on GPIO-E:

- IOE6 (`0x0040`) is SCL.
- IOE7 (`0x0080`) is SDA.
- GPIO-E registers are at `0x7880` through `0x7884`.
- Both lines are open-drain and idle high through board pull-ups.

## Resident implementation

The captured resident module's initializer is at word address `0x037D6C`. It
first probes the BMA222E address and checks chip ID `0xF8`. On that path it sets
the low nibble of BMA register `0x10` to `0xD` and register `0x0F` to `3`, the
configuration used for its bandwidth and plus/minus-2-g range.

The alternative branch probes the Kionix-compatible address and accepts IDs
`0x07` and `0x0A`. It writes `0x40` to register `0x1B`, `4` to register `0x21`,
then `0xC0` to register `0x1B`.

The sample reader at word address `0x037E9D` fetches six consecutive bytes. Its
output conversion is:

```text
x = -(raw_x >> 4)
y =  (raw_y >> 4)
z = -(raw_z >> 4)
```

The helper at `0x037F12` establishes `0x0400` as one g in the normalized
format. BMA222E samples place the significant signed byte in registers `0x03`,
`0x05`, and `0x07`; the even registers contain the unused low bits for this
mode.

## Emulator model

`emulator/src/accelerometer.hpp` implements the BMA222E address, identification
and configuration registers, auto-incrementing register reads and writes,
START/repeated-START/STOP handling, ACKs, and the six-byte XYZ sample. It is
connected to the existing GPIO-E pad and buffer-register model instead of
bypassing the retail driver.

At rest the model reports `(x, y, z) = (0, +0x400, 0)`. Emulator arrow keys
also apply a one-g tilt vector:

| Host key | Normalized motion vector |
|---|---|
| Left | `(-0x400, 0, 0)` |
| Right | `(+0x400, 0, 0)` |
| Up | `(0, 0, +0x400)` |
| Down | `(0, 0, -0x400)` |

Opposite keys cancel on their axis. Releasing all motion keys restores the
neutral gravity vector. Each arrow continues to press its ordinary MobiGo
D-pad matrix cell at the same time.

## Validation

The hardware-accuracy test performs complete bit-level I2C transactions against
the model. It verifies the retail chip ID, a six-byte neutral sample, and all
four arrow directions.

A retail runtime capture was then run unmodified in the emulator. Its resident
driver addressed wire values `0x30`/`0x31`, selected register `0x02` with a
repeated START, and read all six sample bytes. The neutral reply was
`00 00 00 40 00 00`, which the original conversion routine accepts as one g on
Y. No retail program bytes or assets are included in the implementation or
this note.

## Remaining work

- Confirm the exact sensor package fitted to multiple board revisions by
  inspecting hardware markings. The software evidence only proves compatible
  interfaces.
- Add the Kionix-compatible device path if a firmware or board requiring it is
  found. It is documented here but is not needed by the captured runtime.
- Fine-tune tilt magnitude or add analog host input if a title needs gradual
  motion rather than the current digital one-g vectors.
