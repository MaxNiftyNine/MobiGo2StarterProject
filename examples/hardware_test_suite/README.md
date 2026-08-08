# MobiGo 2 SDK hardware test suite

This example builds one donor-free SY-slot MBA that exercises the public SDK
on a physical MobiGo 2. It combines automated checks with short guided tests so
results are visible on the console instead of requiring a debugger.

## Build

From the repository root on macOS/Linux with Wine configured:

```sh
python3 examples/hardware_test_suite/build.py
```

On Windows, run the same command with `py -3`. The result is:

```text
build/hardware-suite/MobiGo2HardwareSuite.MBA
```

To also make an emulator NAND copy:

```sh
python3 examples/hardware_test_suite/build.py --install-nand
```

The suite is intentionally built only for the **SY system slot**. Install it
with recovery media/backups available:

```sh
./scripts/usb/install_mba.command --system \
  build/hardware-suite/MobiGo2HardwareSuite.MBA
```

Replacing the system application is inherently risky. Do not install this MBA
as G1 and do not unplug the console during the USB write.

## Controls and workflow

- Up/Down selects a test.
- Enter starts or confirms.
- Exit records failure/cancels where the screen says it is allowed.
- Help opens the in-session summary.

Run the tests in order. The graphics test deliberately has two steps: it first
shows the family-A tiled background alone, then destroys it and shows family-B
system UI, text, and animation. This reflects the recovered renderer's layer
ordering while keeping every other screen readable.

The final two tests are terminal operations:

- **Application relaunch** launches the installed SY MBA through the resident's
  asynchronous handoff API. The target-side resident API has no known directory
  enumeration or current-application-path service, so the suite probes the two
  bundled, verified region fixtures. Other regional pathnames are **Unknown**
  and the relaunch test reports unsupported rather than inventing a path. A
  volatile title-RAM cookie records pass when that RAM survives the handoff; in
  every case, seeing the suite restart is the authoritative hardware result.
  The suite ends its current frame, finalizes the runtime, and returns from its
  MBA entry after scheduling the request with SY's verified single argument
  `999`.
- **Power off** calls the terminal resident power request. The console shutting
  down is the pass condition; no post-power-cycle marker is required.

The suite does not create, replace, or remove a NAND file. The storage test
opens the existing system list below read-only, reads it twice around an
absolute seek, and compares the data:

```text
A:DEGER\MBASORT.LST
```

This deliberately keeps physical diagnostics non-destructive. Write,
truncate, and remove remain covered against disposable copied NAND by
`make storage-check`; missing-file publication still needs more FTL research.

This target-side relaunch limitation is separate from the host NAND/USB
installers, which enumerate the filesystem and discover slot suffixes without a
numeric regional filename.

## Coverage

| Section | SDK behavior exercised |
| --- | --- |
| Pure self-test | bundle pointer helpers, family-B authoring, bitmap/chunk/RGB555 packing, UI object policy, M-stream writers, ADPCM36 encoder, portable system controls, input pump, and touch parser |
| Graphics | primary bundle registration, family-A create/get/destroy/render, family-B create/get/render, dynamic bundle registration, clean dynamic font, settings/power-off UI, animation transitions |
| Game controls | current/down/pressed/released for Up, Down, Left, Right, Enter, Exit, and Help |
| Keyboard | resident buffered input pointer/count and framework input pump |
| Touch | resident four-word coordinate records and release sentinel |
| System controls | volume/brightness get, set, table mapping, hardware apply, persistence, pressed/down/released, and generated overlays |
| Storage | on hardware: file predicate, read-only open, size, read, absolute seek, repeat read, comparison, and close; on disposable NAND: write, truncate, close/reopen, and remove |
| Effects | PCM8 W effects, S child sequencing, runtime-generated ADPCM36 W effect, handles and playback state |
| Music | M note stream, automatic hardware beat IRQ, program patch, play/state, pause/resume/stop, repeat, level get/set, skip and auxiliary blocks |
| Application | runtime setup/step callbacks, path predicate, argument-bearing SY self-handoff |
| Power | generated power-off presentation and resident shutdown request |

“All” here means every supported public SDK subsystem and authoring surface,
split between safe physical checks and destructive copied-NAND regressions.
Undocumented resident addresses and APIs explicitly marked unverified are not
called merely to inflate coverage. Completion/failure bits live only for the
current run; relaunch may carry one volatile cookie across its software handoff.

## Physical-hardware findings

Testing on 2026-08-01 found and corrected three emulator-only assumptions:

- resident audio query/control return registers are not portable booleans;
  tests now judge written state, handles, audible playback, and aux output;
- creating a fresh diagnostic pathname did not give a reliable persistent
  file, so the physical storage test is now strictly read-only;
- MBA launch schedules an asynchronous handoff, so returning from the service
  call is normal. A follow-up physical run showed that leaving the frame loop
  active keeps the request pending; the callback now returns zero and lets
  resident finalization complete the handoff.

## Source layout

- `main.c` is the fixed-RAM target application and guided state machine.
- `self_tests.c` runs firmware-independent SDK checks on the target CPU.
- `generate_primary_bundle.py` combines original family-A art with the clean
  system UI in one primary linked-resource bundle.
- `build.py` generates resources and invokes the normal SDK/MBA builder.

Generated C, binaries, NAND copies, screenshots, and MBAs stay under `build/`.
