# Emulator and hardware

Emulator2 models the u'nSP CPU, display, DMA, input matrix, touch, audio,
watchdog, NAND, SPI, USB-facing behavior, and MBA overlay used by this starter.

## Build the emulator

The macOS launcher uses the bundled binary when it matches the host. Otherwise
it runs `tools/build/emulator_macos.sh`; install CMake, pkg-config, and SDL2
first. Windows uses `emulator/bin/windows/mobigo2_emu.exe` and its adjacent DLLs.

The source has CTest coverage for audio, watchdog, hardware accuracy, exact
timer/video deadlines, PPU transparency, blending, and fade.

Build it and run those tests with:

```sh
tools/build/emulator_macos.sh --test
```

For a faster Clang build, train profile-guided optimization on the retail boot
path. The script validates all three firmware inputs, records a profile, and
builds `build/emulator-pgo/mobigo2_emu`:

```sh
emulator/pgo_build.sh
```

Set `TRAIN_STEPS` to shorten or lengthen the default 100-million-instruction
training run.

## Accuracy and event timing

The CPU synchronizes peripherals once at each completed instruction. A
deadline scheduler then avoids recalculating every peripheral on instructions
where no hardware-visible event can occur. Reads of live counters force a lazy
synchronization, so this optimization does not quantize timer MMIO values.

The PPU implements RGB555/RGB1555 transparency, 25/50/75/100-percent global
blend levels, individual sprite alpha, fade, and saturation. Frame comparison
and wrap status are generated at programmed scanline-cycle boundaries rather
than host display refresh boundaries.

Windowed desktop runs are paced against cumulative emulated hardware time. The
throttle converts CPU cycles using the currently selected 12 MHz, 32.768 kHz,
or PLL clock and its divider, so the common 48 MHz operating mode is not a
hard-coded instruction-per-second guess. Clock-register changes are segmented
at the instruction that writes them. A host that cannot keep up simply runs
slower.

`--no-window` automatically disables the cap for tests and analysis. Use
`--no-cap` to disable it for a windowed run. VSync, host audio buffering, and
the desktop compositor may still impose their own waits.

## Motion sensor

The MobiGo 2 motion feature is a three-axis accelerometer. The emulator exposes
a BMA222E-compatible device at I2C address `0x18`, connected to the same
GPIO-E pins used by the retail bit-banged driver. It implements chip detection,
configuration-register storage, repeated-start reads, and signed XYZ samples.

The reconstructed resident driver also contains an alternate
Kionix-compatible path at I2C address `0x0F`. The implemented Bosch path reads
chip ID `0xF8` from register `0x00`, then reads six axis bytes beginning at
register `0x02`. Resident code normalizes them as
`x = -(raw_x >> 4)`, `y = raw_y >> 4`, and `z = -(raw_z >> 4)`, with `0x400`
representing one g. The bus is bit-banged on IOE6/SCL and IOE7/SDA.

Host arrow keys drive the large D-pad and a digital tilt at the same time. At
rest, gravity is on positive Y; left/right tilt X and up/down tilt Z. Scripted
`--key-event` arrows use the same dual mapping. See the
[input matrix](reference/INPUT_MATRIX.md) for all bindings and
`research/notes/16_motion_accelerometer.md` for the wire protocol and evidence.

## Browser build

With Emscripten activated, `tools/build/emulator_web.sh` compiles Emulator2 to
WebAssembly and writes the standalone browser build to `emulator/web/dist/`. The default
Pages workflow publishes the development documentation only, keeping the much
larger firmware-backed emulator artifact out of routine documentation deploys.

## Automated checks

The emulator accepts deterministic options including `--no-window`, `--steps`,
`--key-event`, `--dump-frame`, and `--dump-memory`. SDK verification scripts use
these to confirm exact resident state transitions and rendered output.

Run all checks serially with:

```sh
make release-check
```

## Hardware boundary

The from-scratch MBA container is hardware-reported working. The SDK's title
RAM arena and every resident service have stronger emulator evidence than
physical-device coverage; consult `docs/project-status.md` before shipping a game.

Never modify your only NAND or SPI dump. The build creates a separate edited
NAND, and the USB installer has explicit slot and recovery warnings.
