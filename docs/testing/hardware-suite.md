# Guided physical-hardware suite

The maintained hardware suite builds one SY-profile MBA that combines portable
self-tests with guided graphics, controls, keyboard, touch, storage, audio,
music, relaunch, and power checks.

## Build

```sh
python3 examples/hardware_test_suite/build.py
```

The output is:

```text
build/hardware-suite/MobiGo2HardwareSuite.MBA
```

Create a copied NAND first when validating the build:

```sh
python3 examples/hardware_test_suite/build.py --install-nand
```

## Physical installation warning

The suite is SY-linked. It must not be installed as G1. Replacing the physical
system application can prevent normal startup; prepare verified recovery media
and keep power/USB stable.

## Test order

Run visible, reversible tests first:

1. portable self-tests;
2. graphics, UI, text, and animation;
3. game controls and keyboard;
4. touch;
5. system settings;
6. read-only storage;
7. effects and music;
8. application relaunch;
9. power off.

The final two operations intentionally terminate or replace the current run.

The target-side relaunch check supports the two bundled/verified region
fixtures. The published resident storage surface cannot enumerate directories
or ask for the current MBA pathname, so other regions are **Unknown** and must
report the relaunch test as unsupported. Host NAND/USB installers do perform
suffix-based slot discovery; that host capability does not exist inside the
test MBA.

## Storage boundary

Physical storage coverage is deliberately read-only against a known existing
file. Write, truncate, remove, and fresh-create experiments run against copied
NAND. A failed new-path publication must not be converted into repeated physical
writes without FTL evidence.

## Reporting

Record console region/firmware, MBA hash, section result, visible/audible result,
and whether the console restarted or powered down as expected. Do not summarize
a partial run as “all hardware verified.”
