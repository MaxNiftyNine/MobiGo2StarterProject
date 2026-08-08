# MobiGo 2 Homebrew SDK

This manual is the current developer reference for building homebrew that runs
through the MobiGo 2 resident firmware and for understanding the hardware below
it. The project is an independent clean-room effort.

## Start here

From a repository checkout:

```sh
python3 tools/mobigo.py doctor
python3 tools/mobigo.py run
```

The first command explains missing prerequisites. The second builds the default
SY application and boots it through a role-aware in-memory overlay in Emulator2.
Older emulator binaries fall back to a disposable NAND copy.

[Install the prerequisites](start/install.md) or follow the
[first-project walkthrough](start/first-project.md).

!!! warning "SY is the default target"

    G1 is a legacy opt-in profile used by several historical examples. Do not
    copy a G1 entry address, linker profile, device path, or install command
    into a new project. Read [Target profiles](start/target-profiles.md) before
    changing the default.

## Manual map

| Section | Use it for |
| --- | --- |
| [Start](start/install.md) | host setup, first build, repository layout, target choice |
| [Guides](guides/porting.md) | application lifecycle, system behavior, graphics, audio, deployment |
| [API](api/index.md) | public headers, ownership contracts, target-only surfaces |
| [Hardware](hardware/overview.md) | CPU, memory, display, audio, input, storage, registers |
| [Software](software/boot-slots.md) | boot flow, MBA format, resident services, resources, filesystem |
| [Tools](tools/mobigo-cli.md) | unified CLI, emulator, Homebrew Manager, assets, NAND/USB, Ghidra |
| [Testing](testing/test-levels.md) | host, target, emulator, and physical evidence |
| [Examples](examples/index.md) | focused probes and complete projects |
| [Reference](reference/source-confidence.md) | matrices, terminology, limitations, licensing and safety |

## What the SDK supplies

- Donor-free MBA construction for the supported SY and legacy G1 profiles.
- A C API for the resident lifecycle, input, touch, storage, UI resources, and
  audio services.
- Near-automatic Volume, Brightness, and Off behavior through
  `standard_controls.h`.
- A small target-only `hardware.h` layer for high-performance ports that need
  inherited framebuffer, watchdog, DMA, or raw matrix access.
- Deterministic asset generators and emulator verification tools.
- NAND and USB workflows that discover regional slot filenames instead of
  assuming one.
- A light-blue-wave [Homebrew Launcher](examples/homebrew-launcher.md) and a
  backup-first [Homebrew Manager](tools/homebrew-manager.md).

## Evidence policy

Statements are labeled when their evidence boundary matters:

- **Verified** means a named repeatable test or physical observation supports
  the behavior.
- **Emulator-inferred** means source, firmware, or related-chip evidence supports
  it, but physical behavior is not independently established.
- **Unknown** means applications must not depend on an invented answer.

The [capability matrix](testing/capability-matrix.md) is the single current
status ledger. Dated material under `research/` is useful provenance, not the
development source of truth.

## Safe development loop

1. Edit application source.
2. Run `python3 tools/mobigo.py build`.
3. Run `python3 tools/mobigo.py test` when changing shared behavior.
4. Boot through `python3 tools/mobigo.py run`; use `--mode accurate` for
   real-time pacing, diagnostic history, and reference comparison.
5. Exercise rendering, every consumed input, system controls, and any audio or
   storage path.
6. Install on hardware only after copied-NAND tests and recovery preparation.

For a large existing codebase, use the [porting guide](guides/porting.md).
