# Real-hardware SDK test suite

The repository includes a single guided MBA for testing every supported SDK
subsystem on a physical MobiGo 2.

Build it from the repository root:

```sh
python3 examples/hardware_test_suite/build.py
```

Install the resulting `build/hardware-suite/MobiGo2HardwareSuite.MBA` as the SY
system application only after making recovery backups:

```sh
./scripts/usb/install_mba.command --system \
  build/hardware-suite/MobiGo2HardwareSuite.MBA
```

The suite provides guided graphics, controls, keyboard, touch, storage, audio,
music, relaunch, and shutdown checks. It also runs the portable resource,
input, touch, system-control, audio-authoring, and bitmap helpers directly on
the target CPU. Its on-device storage check is deliberately read-only; the
write/truncate/remove checks run against copied NAND with `make storage-check`.

The relaunch service schedules its handoff asynchronously. A return from the
request call is not a launch failure: the frame callback must then return zero
and allow resident finalization to complete the handoff, after which the MBA
entry returns. The suite uses SY's verified single launch argument `999` and
never depends on creating a NAND marker. Seeing it restart is the authoritative
pass condition.

See the
[complete test instructions and coverage matrix](https://github.com/MaxNiftyNine/MobiGo2StarterProject/tree/main/examples/hardware_test_suite)
before installing it. The final relaunch and power-off checks intentionally
restart or stop the console.
