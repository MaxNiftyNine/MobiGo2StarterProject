# THIS IS AI SLOP LIKE EVERYTHING I DO, but it works
im sorry, not sorry.

# MobiGo 2 SDK Starter

A complete C homebrew starter for the VTech MobiGo 2. The project builds the
editable application in [`app/main.c`](app/main.c) against a clean-room SDK,
creates a complete MBA without a donor game, installs it in a copied NAND, and
runs it in Emulator2.

The emulator source already contains the recovered SPU beat and channel
behavior required by SDK music. There is one emulator source tree and one
normal test path—no runtime patch step.

## Quick start

macOS requires Python 3 and Wine:

```sh
./scripts/build_and_run.command --no-audio
```

Windows requires Python 3:

```powershell
.\scripts\build_and_run.ps1 -NoAudio
```

Both commands generate:

```text
build/MobiGo2Starter.MBA
build/nand.edited.bin
```

They never modify the source NAND in `vendor/firmware/`.

## Develop a game

Edit [`app/main.c`](app/main.c). The public SDK is in
[`include/mobigo_sdk`](include/mobigo_sdk), its implementation is in `src/`,
and focused working examples are in [`examples`](examples).

Build without launching the emulator:

```sh
python3 tools/build/build_sdk_app.py app/main.c \
  --output-dir build \
  --name MobiGo2Starter \
  --slot SY
```

Useful options include `--slot G1`, repeatable `--extra-source` for C or u'nSP
assembly files,
`--with-clean-font`, and custom `--menu-tile`/`--palette` data.

Three complete G1 projects ported from the original toolkit are maintained in
[`examples`](examples): Color Cycle, the monochrome movie player, and MobiGo
Celeste. Build all three with `make samples`.

An MBA handoff does not run a conventional initialized-data C startup. Keep
large immutable assets `const`, explicitly initialize mutable state, and do not
return from a resident application. The starter demonstrates the safe pattern.

## Test

Fast host tests:

```sh
make test
```

Complete compiler, emulator, graphics, storage, input, and audio verification:

```sh
make release-check
```

The emulator itself is tested directly with:

```sh
tools/build/emulator_macos.sh --test
```

## Hardware and Ghidra

USB installation and recovery guidance is in
[`tools/usb/README.md`](tools/usb/README.md). Install the default SY build with:

```sh
./scripts/usb/install_mba.command --system build/MobiGo2Starter.MBA
```

For a guided real-console check of every supported SDK subsystem, build the
[`examples/hardware_test_suite`](examples/hardware_test_suite) project or run
`make hardware-suite`.

The MBA/GAM Ghidra extension is in
[`tools/ghidra/loader/MobiGoMbaLoader`](tools/ghidra/loader/MobiGoMbaLoader).
Analysis helpers are kept separately in `tools/ghidra/scripts/`.

## Documentation

[Click Here for docs](https://maxniftynine.github.io/MobiGo2StarterProject/)

The GitHub Pages source is [`docs`](docs), configured by `mkdocs.yml`. Locally:

```sh
python3 -m pip install -r docs/requirements.txt
mkdocs serve
```


## Layout

```text
app/             editable starter application
include/, src/   public SDK and implementation
examples/        focused probes, a hardware suite, and complete sample projects
tests/           firmware-free SDK and packaging tests
emulator/        Emulator2 source, tests, web frontend, and platform binaries
tools/           build, asset, NAND, USB, RE, verification, and Ghidra tools
scripts/         user-facing macOS and Windows launchers
docs/            published guides and technical references
research/        RE notes, reports, archived material, and experimental probes
vendor/          Generalplus tools/linker bodies and device firmware
```

See [`docs/project-status.md`](docs/project-status.md) for exact evidence and
known limitations. Read [`THIRD_PARTY.md`](THIRD_PARTY.md) before redistribution.
