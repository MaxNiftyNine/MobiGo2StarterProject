# Emulator2 workflows and modes

Emulator2 boots the supplied ROM/SPI/NAND firmware, interprets the u'nSP CPU,
and models the display, DMA, input matrix, touch, motion, timers, watchdog,
audio, storage, USB, and MBA handoff paths used by this SDK.

## Recommended application run

```sh
python3 tools/mobigo.py run --mode fast
python3 tools/mobigo.py run --mode accurate
```

Use fast mode during ordinary iteration and accurate mode for real-time pacing,
diagnostic history, timing observation, and release smoke tests.

### Accurate mode

- preserves real-time pacing by default;
- retains recent PC/instruction history for failure diagnosis;
- retains the full CPU/peripheral synchronization and normal presentation rate.

### Fast mode

- disables the real-time cap by default;
- disables recent-history tracking unless logging/tracing needs it;
- does not skip CPU instructions or disable peripheral state advancement.

Both modes map arrows only to the D-pad. Home, End, Page Up, and Page Down are
the dedicated left, right, up, and down accelerometer bindings. Modes change
host pacing and diagnostic bookkeeping, not guest input or peripheral behavior.

Performance mode is a host execution policy, not a different MBA ABI.

## Role-aware MBA overlay

Current emulator builds accept an MBA plus `--mba-target auto`. The loader reads
the role and applies the file only in memory to the matching application slot.
It does not edit the source NAND and does not pretend a G1 MBA is an SY or MM
application.

The unified CLI uses this path automatically and falls back to a copied NAND for
older binaries.

## Source build

On macOS and Linux:

```sh
bash tools/build/emulator_unix.sh --test
```

The script configures a release CMake build, compiles Emulator2, and optionally
runs CTest. On Windows, the unified CLI invokes the corresponding CMake/Ninja
builder in `tools/build/emulator_windows.py` and writes the executable under
`build/emulator-host/`.

The source is maintained as the `emulator/` submodule and as the standalone
[MobiGo2Emulator repository](https://github.com/MaxNiftyNine/MobiGo2Emulator).
Its releases contain firmware and host runtime libraries, so a downloaded
package starts by opening the executable; no command line is required. Set
`MOBIGO_EMULATOR` to a standalone executable when using it with this SDK.

## Deterministic headless options

Useful direct options include:

- `--no-window` and `--steps` for bounded execution;
- `--key-event` and `--touch-event` for scripted input;
- `--dump-frame` and `--dump-frame-dir` for visual evidence;
- `--dump-memory`, base, and length for state evidence;
- `--trace` and filtered trace ranges for CPU diagnosis;
- `--audio` for host playback; silent runs still advance audio hardware state.

Verification scripts under `tools/verify/` construct exact commands and assert
frames or memory. Prefer extending those scripts over parsing an interactive
window manually.

## Browser build

With Emscripten activated:

```sh
bash tools/build/emulator_web.sh
```

Outputs are written under `emulator/web/dist/`. Firmware-backed artifacts are
not part of the routine documentation deployment.

## Performance work

Profile-guided builds and the event-deadline scheduler improve host speed
without changing application format. Benchmark with a fixed firmware set,
instruction count, mode, final cycle count, PC, and registers. A host MIPS value
without those controls is not a correctness result.
