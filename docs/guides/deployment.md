# Deploy and recover safely

Routine development uses a role-aware in-memory emulator overlay. Persistent
copied-NAND testing and physical installation are separate, higher-risk levels.

## Routine emulator workflow

```sh
python3 tools/mobigo.py run
```

The unified command builds the SY application and asks current Emulator2 builds
to apply it through a role-aware in-memory overlay. The role is read from the
MBA; the CLI does not cross-install SY into G1. Older emulator binaries fall
back to a verified edited NAND automatically.

Create a persistent copied NAND explicitly with:

```sh
python3 tools/mobigo.py build --nand
```

The tracked split parts and assembled source image are not modified by either
path.

## Before using a physical console

1. Keep verified internal ROM, SPI, and NAND recovery copies.
2. Confirm the application profile with the build output.
3. Run the complete copied-NAND emulator path.
4. Test standard controls and every terminal operation.
5. Confirm the USB tool detects the expected MobiGo device.
6. Keep power and USB stable during every write.

## Install targets

- `--system` discovers and replaces the existing SY application. Use only an
  SY-linked MBA. A broken SY can prevent normal startup.
- `--g1` discovers and replaces the existing G1 application. Use only a
  G1-linked MBA.
- `--root` writes a named root file for developer-mode workflows. It does not
  convert the MBA's profile.

The installer discovers the regional filename. Do not supply a hard-coded slot
pathname from a trace or another console.

Both NAND and USB installers validate the complete launcher metadata before a
persistent SY or G1 replacement. A known cross-slot profile is always rejected.
Unknown/custom metadata also fails closed; `--allow-unverified-profile` is only
for a manually reviewed unknown profile and cannot override a known SY↔G1
mismatch.

## Terminal operations

Power-off and asynchronous application relaunch intentionally stop or replace
the current application. Test them last. A launch request must be followed by a
zero frame return, resident finalization, and the correct MBA-entry return.

## Failure handling

If a copied-NAND boot fails, preserve the generated MBA, edited NAND, command
output, emulator log, and deterministic step count. Do not “fix” the failure by
changing to G1 or injecting the binary around normal boot; that would test a
different contract.

If a physical write is interrupted or the console no longer boots, stop making
additional writes and use the prepared recovery procedure and untouched dumps.
