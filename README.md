# MobiGo 2 Homebrew SDK

Build C homebrew for the VTech MobiGo 2, package it as a donor-free MBA,
install it into a disposable NAND image, and test it in Emulator2.

The supported starting point is the editable application in `app/main.c`. New
projects target the **SY system profile** unless they deliberately opt into the
legacy G1 compatibility profile. SY and G1 binaries are not interchangeable.

## Quick start

Clone the repository with its maintained emulator and manager repositories:

```sh
git clone --recurse-submodules https://github.com/MaxNiftyNine/MobiGo2StarterProject.git
cd MobiGo2StarterProject
```

For an existing clone, run `git submodule update --init --recursive` once.

The canonical command-line entry point is:

```sh
python3 tools/mobigo.py doctor
python3 tools/mobigo.py run
```

`doctor` checks the host, target compiler, firmware inputs, and emulator.
`run` builds the starter, applies a role-aware in-memory MBA overlay, and
launches the emulator. Older emulator binaries automatically fall back to a
verified copied-NAND install. Neither path changes tracked firmware inputs.

Other common commands are:

```sh
python3 tools/mobigo.py build
python3 tools/mobigo.py test
```

- `build` produces `build/MobiGo2Starter.MBA` and related artifacts without
  launching the emulator. Add `--nand` when a persistent edited NAND is needed.
- `test` runs host, USB, target-compiler, emulator unit, and emulator-device
  checks. Add `--full` for all firmware integrations, sample builds, and
  complete-sample emulator runtime checks.

On stock Windows without Make, `test` labels and runs a smaller native baseline
that still includes target compilation and a firmware/emulator integration.
The full command fails until the documented MSYS2 test prerequisites are present;
it never reports success after silently skipping release checks.

See the [installation guide](docs/start/install.md) for Windows, macOS, and
Linux prerequisites and the [first-project guide](docs/start/first-project.md)
for the complete workflow.

## Develop a game

Edit `app/main.c` or copy the starter into a new project. Public headers are in
`include/mobigo_sdk/`; implementations are in `src/`.

Target applications are C: the bundled builder supports C99-style `.c` and
u'nSP `.asm`/`.s` sources. It does not provide a target C++ frontend or an
established C++ ABI. Emulator2 is independently written in host C++20.

The SDK includes:

- the resident application lifecycle;
- logical buttons, keyboard input, touch, and motion-sensor support;
- standard volume, brightness, and power-off handling;
- graphics resources, sprites, animation, and text;
- PCM8 and ADPCM36 effects plus sequenced music;
- resident storage access;
- donor-free SY and legacy G1 MBA packaging;
- NAND, USB, asset, emulator, and Ghidra tools.

Read [Lifecycle and memory](docs/guides/lifecycle-memory.md) before porting code.
A direct MBA entry does not receive conventional C runtime initialization, so
ordinary assumptions about initialized writable globals are unsafe.

For a substantial port, start with the
[porting guide](docs/guides/porting.md). It is written for both human developers
and coding agents.

## Targets and installation safety

The default starter is linked for SY. Use the role-aware emulator workflow for
normal development and a copied NAND when validating persistent installation.
Installing an SY application on a physical device replaces
the system menu and requires verified recovery backups.

G1 is a legacy, explicit opt-in used by several examples. A G1-linked MBA must
be installed with the G1 target; never install the default SY artifact as G1.
Device filenames differ by region, so use the filesystem-aware tools instead of
embedding a numeric slot filename in code, documentation, or automation.

See [Target profiles](docs/start/target-profiles.md) and
[Deployment and recovery](docs/guides/deployment.md).

## Test before hardware

Run:

```sh
python3 tools/mobigo.py test
```

Every port should also receive an application-specific emulator smoke test.
Input, rendering, system controls, audio, storage, shutdown, and relaunch paths
that the application uses should be exercised before physical installation.
The [testing guide](docs/testing/test-levels.md) explains the available levels
and their evidence boundaries.

## Documentation

The published manual is at
[maxniftynine.github.io/MobiGo2StarterProject](https://maxniftynine.github.io/MobiGo2StarterProject/).
It separates application development, API reference, physical hardware,
firmware/software behavior, tools, and validation evidence.

Build it locally with:

```sh
python3 -m pip install -r docs/requirements.txt
mkdocs serve
```

Historical reverse-engineering notes remain under `research/`. They preserve
evidence but are not the source of truth for new application paths.

## Repository layout

```text
app/             editable SY starter application
include/, src/   public clean-room SDK and implementation
examples/        focused probes and complete opt-in examples
tests/           firmware-free SDK and packaging tests
emulator/        MobiGo2Emulator submodule
tools/           unified CLI, specialist tools, and Homebrew Manager submodule
scripts/         compatibility launchers for desktop workflows
docs/            current published manual
research/        evidence, dated notes, reports, and historical material
vendor/          third-party tools, linker profiles, and firmware inputs
```

Read `THIRD_PARTY.md` before redistributing the repository or its bundled
inputs. The project is an independent clean-room effort, not an official VTech
or Generalplus SDK.

Standalone tools and packaged releases:

- [MobiGo2Emulator](https://github.com/MaxNiftyNine/MobiGo2Emulator)
- [MobiGo2HomebrewManager](https://github.com/MaxNiftyNine/MobiGo2HomebrewManager)
