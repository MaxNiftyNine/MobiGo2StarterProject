# Homebrew Launcher

Homebrew Launcher is an SY-profile menu for `.MBA` applications stored below
`/HB`. It keeps each application's `.MBA` filename visible, uses a light-blue
animated wave background, and preserves the standard volume, brightness, and
power controls.

The retail application API does not expose verified directory enumeration.
Homebrew Manager therefore writes `/HB/INDEX.HB` as a compact catalog whenever
an application is added, renamed, or removed. The launcher validates that
catalog before displaying up to 16 applications. The original system menu is
listed as `System.MBA` after a manager installation.

Build it from source:

```sh
python3 examples/homebrew_launcher/build.py
```

The output is `build/homebrew-launcher/HomebrewLauncher.MBA`.

| Action | Control |
| --- | --- |
| Select | Up or Down |
| Change page | Left or Right |
| Launch | Primary or Enter |
| System behavior | Volume, Brightness, and Off |

Run its deterministic firmware test with:

```sh
make launcher-emulator-check
```

That test overlays the launcher without editing the source NAND, validates the
catalog and wave presentation, launches multiple indexed `.MBA` entries, and
checks the follow-up application handoff.

Use [Homebrew Manager](../tools/homebrew-manager.md) for backup-first physical
installation. Do not overwrite SY manually without a verified recovery copy.
