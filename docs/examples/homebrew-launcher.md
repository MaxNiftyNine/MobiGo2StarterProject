# Homebrew Launcher

Homebrew Launcher is an SY-profile menu for `.MBA` applications stored below
`/HB`. Its deliberately simple screen contains a fast, light-blue animated wave
background and a three-item horizontal carousel along the bottom. Each item is
only the application's name and the real 64×104 menu artwork embedded in that
MBA at offsets `0xA0` and `0xC0`; the launcher has no substitute icon set. A
small PCM8 version of the supplied menu track loops while the menu is open.
Volume, brightness, and power controls remain active.

The retail application API does not expose verified directory enumeration.
Homebrew Manager therefore writes `/HB/INDEX.HB` as a compact catalog whenever
an application is added, renamed, or removed. The launcher validates that
catalog before displaying up to 16 applications. It reads the title from
`HB02` and retains read compatibility with `HB01`; old description, author, and
icon-id fields are ignored. The original system menu remains the executable
`/HB/System.MBA` and appears as an intentionally text-only carousel item after
a manager installation; all other entries use their baked MBA icon.

Build it from source:

```sh
python3 examples/homebrew_launcher/build.py
```

The output is `build/homebrew-launcher/HomebrewLauncher.MBA`.

| Action | Control |
| --- | --- |
| Select previous/next | Left or Right |
| Select | Tap a side icon |
| Launch | Tap the selected center icon |
| Launch selected | Primary or Enter |
| System behavior | Volume, Brightness, and Off |

Run its deterministic firmware test with:

```sh
make launcher-emulator-check
```

That test overlays the launcher without editing the source NAND, validates the
catalog and MBA-header artwork path, proves multiple distinct wave frames,
observes the embedded PCM8 song start with repeat enabled, injects a carousel
tap, and checks the follow-up application handoff.

Use [Homebrew Manager](../tools/homebrew-manager.md) for backup-first physical
installation. Do not overwrite SY manually without a verified recovery copy.
