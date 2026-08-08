# Repository guidance for coding agents

This file is the operational contract for automated work in this repository.
Read it before modifying application, SDK, emulator, build, or documentation
code.

## Canonical workflow

Use the unified command from the repository root:

```sh
python3 tools/mobigo.py doctor
python3 tools/mobigo.py build
python3 tools/mobigo.py run
python3 tools/mobigo.py test
```

- `doctor` diagnoses host and repository prerequisites.
- `build` creates the default donor-free SY application.
- `run` builds, applies a role-aware transient MBA overlay, and starts
  Emulator2. A persistent copied NAND is explicit validation, not the default.
- `test` runs host, USB, target-compiler, emulator unit, and emulator-device
  checks. `test --full` adds every firmware integration, sample build, and
  complete-sample emulator runtime check.

Specialist scripts remain useful for debugging, but do not create a parallel
build path when the unified CLI can express the operation.

## Target invariant

**New projects target SY.** Do not switch a new application to G1 because an
older example or research note uses it.

G1 is a legacy, explicit opt-in profile. A G1 payload and an SY payload have
different entry addresses, protected regions, launcher metadata, and install
targets. They are not interchangeable.

Never hard-code regional device filenames. Use the NAND/USB installer's slot
discovery. A literal filename in research evidence is not a reusable path.

Read `docs/start/target-profiles.md` before changing a slot or install workflow.

## Application invariants

- The editable starter is `app/main.c`.
- Target application code is C99-style C plus optional u'nSP `.asm`/`.s`.
  Do not introduce C++ target files or assume the host emulator's C++20 ABI.
- A direct MBA handoff is not a conventional reset-time C startup. Do not rely
  on initialized writable globals or an automatically cleared BSS.
- Keep large immutable assets `const`. Explicitly initialize mutable state in
  application-owned title RAM.
- Use the resident setup/step/finalize lifecycle and obey its callback return
  contract.
- Do not disable inherited interrupts or neglect the watchdog during a
  low-level loop.
- Prefer logical resident input over raw matrix scanning.
- Prefer resident graphics/resources over direct PPU programming when using the
  resident lifecycle.

## Standard system behavior

New applications should use `mobigo_sdk/standard_controls.h` for the standard
Volume Up, Volume Down, Brightness, and Off experience. Initialize it once with
writable bundle RAM and poll it once per resident frame.

A direct framebuffer loop that does not step resident UI should use
`mobigo_sdk/direct_controls.h`. It scans matrix edges and delegates settings,
hardware application, persistence, and power-off to resident services, but it
cannot draw resident overlays. Do not use it as a shortcut in a normal resident
application.

Use `system_controls.h` only when implementing a custom platform backend or
presentation layer. Do not map a game action onto a system button without also
preserving the system behavior expected for that button.

## Low-level ports

`mobigo_sdk/hardware.h` is the supported target-only surface for watchdog,
inherited framebuffer, DMA, and raw matrix operations. Use it for ports that
intentionally own their frame loop or need predictable bulk copies. Do not
duplicate MMIO constants inside a port when a helper exists.

Direct hardware access and resident services can have different ownership
assumptions. State which model the port uses and avoid mixing them casually.

## Testing requirement

Do not claim a port works because it compiles. At minimum:

1. run the host and target checks through `python3 tools/mobigo.py test`;
2. boot the generated MBA through the canonical transient role-aware overlay;
3. exercise every input the application consumes;
4. verify representative rendering and frame progression;
5. test standard volume, brightness, and Off behavior;
6. test audio and storage when used;
7. add a deterministic emulator regression for the port's critical path.

Add copied-NAND parity or installation validation when the change touches
packaging, filesystem behavior, slot discovery, or persistent installation.

Physical testing is an additional evidence level, not a replacement for
repeatable emulator checks. Never modify the only copy of a NAND or SPI dump.

## Evidence and uncertainty

Use these labels consistently:

- **Verified**: covered by a named test or a reproducible hardware observation.
- **Emulator-inferred**: implemented from emulator, firmware, or related-chip
  evidence but not independently confirmed on the physical device.
- **Unknown**: insufficient evidence; do not invent behavior.

The current capability matrix is `docs/testing/capability-matrix.md`. Historical
notes under `research/` can explain why a decision was made, but they do not
override current headers, tests, or published guides.

## Scope discipline

- Preserve unrelated user changes in a dirty worktree.
- Keep generated files under `build/`.
- Do not copy retail payloads into clean-room source or tests.
- Update documentation and capability evidence with API or behavior changes.
- Use current repository paths. Do not resurrect retired G1-specific wrappers,
  private linker bodies, obsolete USB-directory aliases, or root-level build
  scripts.

For a large port such as Doom, follow `docs/guides/porting.md` before writing
platform code.
