# Deterministic emulator validation

The emulator accepts bounded, scriptable input and output options so integration
checks do not depend on a person watching a window.

## Run mode

Use accurate mode for real-time pacing/diagnostic history and fast mode for
routine throughput. Guest input mappings are identical. Verification scripts
should name the mode explicitly so a future default change cannot silently
alter pacing or diagnostic bookkeeping.

## Inputs

Scripted button/keyboard events use:

```text
--key-event instruction,duration,name
```

Touch events use:

```text
--touch-event instruction,duration,x,y
```

Event ranges must be bounded and non-overlapping where required. Use names from
the [input matrix](../reference/input-matrix.md). `--key-event` controls matrix
switches only. Interactive motion uses Home, End, Page Up, and Page Down in
both modes; do not pass invented motion names to `--key-event`.

## Outputs

Useful assertions include:

- exact pixels or regions in `--dump-frame` output;
- a marker in a bounded `--dump-memory` range;
- resident handles and state transitions;
- file contents after close/reopen in a copied NAND;
- audio channel/state values and natural completion;
- process exit and absence of reset/watchdog failure.

Do not use a final PC alone as application success; a loop, reset, or firmware
screen can be stable at the wrong state.

Run `make sample-emulator-check` to build and boot all complete examples. The
check asserts the correct SY or legacy G1 role, bounded payload execution,
visible frame output and progression, representative game input, and direct
Off behavior where applicable. Its artifacts are written below `build/`.

## Normal application route

Tests should use role-aware transient loading or a copied-NAND install that
matches the MBA profile. Do not inject an SY application into G1 because that
reaches an address. The loader role and filesystem behavior are part of the
contract.

## Failure artifacts

A verification script should preserve or print:

- complete emulator command;
- selected mode and instruction count;
- emulator log path;
- frame/memory dump paths;
- expected versus observed values;
- generated MBA and NAND paths.

This makes regressions reproducible on Windows, macOS, and Linux hosts.
