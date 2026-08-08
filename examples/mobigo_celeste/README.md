# MobiGo Celeste

This advanced G1 example ports the `ccleste` C translation of Celeste Classic
to MobiGo 2. It renders into a packed 128x128 PICO-8-style framebuffer and uses
an optimized u'nSP assembly scaler plus system DMA to present a centered
240x240 image.

## Controls

| Action | Console controls | Keyboard alternatives | Emulator host keys |
| --- | --- | --- | --- |
| Move left/right | large D-pad or keyboard arrows | A / D | arrows, A / D, `[` / `]` |
| Move up/down | large D-pad | W / S | arrows, W / S |
| Jump/start | Primary or Enter | E | Ctrl, Return, E |
| Dash | Help or Brightness | X or Space | F1, F6, X, Space |

Brightness retains its system behavior while also triggering dash. Volume Up,
Volume Down, Brightness, and Off are polled through `direct_controls.h`; direct
framebuffer ownership means no resident overlay is drawn.

## Build

From the repository root:

```sh
python3 examples/mobigo_celeste/build.py
```

The complete donor-free MBA is written to
`build/celeste/MobiGoCeleste.MBA`. Add `--install-nand` to also create a NAND
image with the sample installed in the G1 slot.

The standard SDK builder now accepts `.asm` files through repeated
`--extra-source` arguments; this project does not carry its own linker body or
old PowerShell toolchain wrapper.

## Assets and provenance

`src/assets.h` is the checked-in compiler-ready asset header. To regenerate it
after editing the files under `reference/`, install Pillow and run:

```sh
python3 examples/mobigo_celeste/tools/generate_assets.py
```

Celeste Classic, the original PICO-8 cartridge, `ccleste`, and their artwork
remain subject to their respective owners' rights. This port is included as a
technical, noncommercial homebrew example; review those upstream terms before
redistributing it.
