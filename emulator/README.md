# Emulator2

Emulator2 is the repository's C++20 host emulator for the GPL16250-class MobiGo
2 environment. It boots the supplied ROM/SPI/NAND firmware and models the CPU,
display/PPU, DMA, matrix input, touch, accelerometer, timers, watchdog, audio,
storage, USB, and role-aware MBA handoff paths used by the SDK.

For application development, use the unified command from the repository root:

```sh
python3 tools/mobigo.py run
```

That command builds the configured SY application, applies a transient
role-aware overlay, and opens the emulator at the selected application. It does
not modify the source NAND. See
[`docs/tools/emulator.md`](../docs/tools/emulator.md) for the maintained workflow
and evidence boundaries.

## Build the host emulator

On macOS or Linux, install CMake, a C++20 compiler, SDL2, and `pkg-config`, then
run:

```sh
bash tools/build/emulator_unix.sh --test
```

The release binary is written under `build/emulator-host/`; `--test` also runs
the CTest device/unit suite. Windows users can use the checked-in 64-bit binary
and adjacent SDL2/MinGW runtime DLLs under `emulator/bin/windows/`. A Windows
source build needs a C++20 toolchain plus SDL2 discoverable through
`pkg-config`; configure `emulator/CMakeLists.txt` with `BUILD_TESTING=ON` and run
CTest before replacing the distributed binary.

For a profile-guided Clang build:

```sh
sh emulator/pgo_build.sh
```

This trains against the verified firmware inputs and writes the optimized
binary under `build/emulator-pgo/`. Benchmark correctness with fixed firmware,
instruction count, final cycle count, PC, and registers—not host MIPS alone.

## Direct role-aware launch

The unified CLI is preferred. For emulator diagnosis, the equivalent direct
shape is:

```sh
build/emulator-host/mobigo2_emu \
  --rom vendor/firmware/internalrom.bin \
  --spi vendor/firmware/spi.bin \
  --nand vendor/firmware/nand.us-stitched.bin \
  --mba build/MobiGo2Starter.MBA \
  --mba-target auto \
  --open-window-on-mba \
  --mode accurate
```

`--mba-target` accepts `auto`, `system`, `g1`, or `menu` (plus the documented
role aliases). `auto` reads the MBA's role metadata. The loader never treats an
SY binary as G1 merely because a different slot was requested. `--mba-slot` is
a compatibility alias; new scripts should use `--mba-target`.

The overlay exists in memory only. Use `python3 tools/mobigo.py build --nand`
when the behavior under test is persistent installation, suffix-based slot
discovery, or filesystem mutation.

## Accurate and fast modes

Both modes execute the same CPU/peripheral implementation and expose identical
guest input:

- `--mode accurate` enables real-time pacing and recent diagnostic history by
  default;
- `--mode fast` disables the cap and unneeded history bookkeeping by default.

Explicit `--cap`/`--no-cap` can override pacing. Headless runs are uncapped.
Fast mode does not skip guest instructions, device deadlines, audio state, or
input events. Accurate mode is not a claim of cycle-perfect/electrical fidelity.

## Host controls

| MobiGo 2 input | Host control |
| --- | --- |
| Large D-pad | arrows |
| Accelerometer left/right/up/down | Home / End / Page Up / Page Down |
| Primary | left or right Ctrl |
| Exit | Escape |
| Help | F1 |
| Off | F2 |
| Brightness | F6 |
| Volume Down / Up | F7 / F8 |
| Keyboard letters | matching host letters |
| Keyboard Left / Right | `[` / `]` |
| Enter / Delete / Space / Question | Return / Backspace / Space / `/` |
| Touchscreen | left mouse button and drag |
| Close emulator | F12 |

Arrows are D-pad only in both modes. The complete physical matrix and scripted
names are in
[`docs/reference/input-matrix.md`](../docs/reference/input-matrix.md).

## Deterministic validation

Headless checks can bound execution and inject matrix/touch events:

```sh
build/emulator-host/mobigo2_emu ... \
  --mode fast --no-window --steps 50000000 \
  --key-event 1000000,20000,primary \
  --touch-event 2000000,10000,160,120 \
  --dump-frame build/frame.bmp
```

`--key-event` accepts matrix names only; it does not synthesize motion. Useful
assertion outputs include `--dump-frame`, `--dump-current-frame`,
`--dump-frame-dir`, `--dump-memory`, `--dump-code`, filtered trace/log options,
and terminal process state. Verification scripts under `tools/verify/` provide
reproducible commands and expected frames/state.

Host audio is opt-in with `--audio`. Silent/headless execution still advances
SPU/DAC state, completion, and interrupt scheduling.

## USB model

`--usb` enables the firmware-mediated mass-storage/mailbox model. In a windowed
run, press `U` to open its host-control panel. Commands traverse emulated USB,
DMA, and firmware filesystem paths; they do not patch guest NAND behind the
firmware. Writes are read back for exact verification.

Use `--usb` only with a disposable NAND copy: a clean exit can atomically save
guest NAND changes to the supplied `--nand` path. A transient `--mba` overlay is
not written back.

## Browser build

With Emscripten activated:

```sh
bash tools/build/emulator_web.sh
```

Output is written to `emulator/web/dist/`. The build preloads firmware-derived
inputs, so it is not automatically suitable for public hosting or the normal
documentation deployment. Confirm redistribution rights first.

## Fidelity and research

The emulator is correctness-oriented but incomplete. Passing it proves behavior
against the modeled firmware/hardware path, not every physical console revision
or analog/electrical edge. Current status and open gaps live in
[`docs/testing/capability-matrix.md`](../docs/testing/capability-matrix.md) and
[`docs/reference/known-limitations.md`](../docs/reference/known-limitations.md).
Chronological implementation evidence belongs in `emulator/DISCOVERY.md`; it is
not the source of truth for current application commands or target defaults.
