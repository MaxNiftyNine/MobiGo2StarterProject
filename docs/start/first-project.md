# Build and run the first project

The checked-in starter uses the resident application lifecycle and the standard
system-control presentation. It is the canonical base for a new project.

## 1. Check the checkout

```sh
python3 tools/mobigo.py doctor
```

Resolve required failures before building. Optional warnings only matter when
you use the related feature.

## 2. Build without launching

```sh
python3 tools/mobigo.py build
```

The default profile is SY. The expected product is:

```text
build/MobiGo2Starter.MBA
```

Add `--nand` to also produce `build/nand.edited.bin`. The source NAND remains
unchanged.

## 3. Run through normal firmware boot

```sh
python3 tools/mobigo.py run
```

Current Emulator2 builds apply the MBA in memory according to its role and open
the window when that application is reached. The CLI requires that built-in
launch path and reports an actionable error for an outdated emulator. Use
`python3 tools/mobigo.py build --nand` when testing persistent filesystem
installation itself.

The editable starter is intentionally a blank application rather than a demo
game. Its clean black frame is expected. Press F8 for Volume Up or F6 for
Brightness in the emulator to verify the generated system overlay, then add
your own scene in `app/main.c`.

## 4. Edit the application

Open `app/main.c`. Keep these constraints intact:

- immutable tables and assets should be `const`;
- writable state must be explicitly initialized in application-owned memory;
- setup, frame, and stop callbacks run under the resident lifecycle;
- the frame callback must continue returning nonzero until the application
  deliberately exits or completes a scheduled handoff;
- standard controls must be polled every frame;
- do not return from the MBA entry into an accidental relaunch loop.

Read [Lifecycle and memory](../guides/lifecycle-memory.md) for the reason behind
these rules.

## 5. Add source and generated assets

The unified build discovers the starter project configuration. Specialist
builds can still pass additional C or u'nSP assembly sources through the SDK
builder:

```sh
python3 tools/build/build_sdk_app.py app/main.c \
  --output-dir build \
  --slot SY \
  --name MyGame \
  --extra-source path/to/generated_resources.c
```

Prefer the unified CLI for routine work. Use the specialist script when
debugging the lower-level pipeline or when a project has not yet moved to the
project configuration.

## 6. Test behavior

```sh
python3 tools/mobigo.py test
```

Then manually or deterministically exercise:

- every game control and keyboard alternative the application accepts;
- touch and motion if used;
- Volume Up, Volume Down, Brightness, and Off;
- visible frame progression and scene transitions;
- every audio class and storage operation the application uses.

For automated input and framebuffer checks, see
[Emulator validation](../testing/emulator-validation.md).

## 7. Rename or split the project

Once the first run succeeds, rename the artifact in the project configuration,
move application-specific source out of `app/` if desired, and add a dedicated
emulator smoke test. Keep the SY profile unless the project has a concrete G1
compatibility requirement.
