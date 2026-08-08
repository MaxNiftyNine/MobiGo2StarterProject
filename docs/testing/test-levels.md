# Test levels and release evidence

Different tests answer different questions. A green host unit test does not prove
a firmware ABI, and an emulator screenshot does not prove physical behavior.

## Canonical commands

```sh
python3 tools/mobigo.py test
python3 tools/mobigo.py test --full
```

The normal command runs host and USB tests, a target-compiler check, emulator
unit tests, and emulator device/integration tests. The full command adds every
firmware integration check, all sample builds, and deterministic runtime checks
for every complete sample. Documentation has its own `make docs-check` gate and
release automation composes both commands.

Stock Windows without Make runs a clearly labeled native baseline for the
normal command. It includes Python/USB tests, full target-object compilation,
the configured build, and one firmware/emulator integration. `--full` fails
until the documented Make/MSYS2 host-C and Emulator2 CTest prerequisites are
available; a partial run is never reported as a full pass.

## Evidence ladder

| Level | What it proves | What it does not prove |
| --- | --- | --- |
| Static/config | paths, manifest, formatting, generated metadata | compiled or runtime behavior |
| Host unit | portable C/Python logic and error cases | target ABI or firmware calls |
| Target compile | Generalplus compiler accepts public/target source | application executes correctly |
| Emulator CTest | isolated CPU/peripheral model behavior | complete firmware integration |
| Firmware integration | normal firmware reaches expected state/frame | physical electrical behavior |
| Copied NAND | package, filesystem install, loader, and application agree | USB or physical console behavior |
| Physical guided test | observed behavior on tested console/firmware | every revision or untested edge case |

## Make targets

The Makefile retains narrow developer targets such as `test`, `target-check`,
`emulator-test`, system UI/input/storage/font/animation/audio/music checks,
`samples`, `sample-emulator-check`, and `hardware-suite`. `release-check`
composes the full set.

Use a narrow target while iterating. Use the unified full command before a
release claim.

## Application-specific requirement

The repository suite cannot know a new game's controls, scenes, or success
markers. Every substantial port needs a deterministic integration script that:

1. builds the configured target;
2. boots it through the supported application role;
3. injects representative input;
4. waits for bounded progress;
5. asserts a frame or memory result;
6. fails with the command/log/artifact locations needed for diagnosis.

Also verify standard controls for every application, even if gameplay itself
does not use system buttons.

## Documentation checks

`make docs-check` validates the canonical site URL/configuration, internal
Markdown links and repository paths, forbidden conversational/self-deprecating
phrases, and a strict MkDocs build when MkDocs is installed.

## Recording results

Update the [capability matrix](capability-matrix.md) only with a named repeatable
test or a dated physical observation. Keep “not tested” distinct from “failed”
and “not implemented.”
