# Complete project examples

!!! warning "Mixed target profiles"

    Color Cycle builds for canonical SY. The movie player and Celeste remain
    explicit legacy G1 compatibility projects. Start a new project from
    `app/main.c` and retain SY unless G1 compatibility is a stated requirement.

## Color Cycle

`examples/color_cycle/` is the smallest low-level framebuffer demonstration. It
captures the launcher-selected display buffers, fills through system DMA,
preserves interrupt behavior, services the watchdog, and polls direct system
controls without resident overlays.

```sh
python3 examples/color_cycle/build.py
```

Output: `build/color-cycle/ColorCycle.MBA`, linked for SY.

Use it to study direct framebuffer ownership, not target selection or the
resident game template.

## Monochrome movie player

`examples/bad_apple_player/` plays a 64×48 one-bit XOR-delta/RLE movie scaled to
320×240 with unsigned PCM audio. The default build creates an original synthetic
clip and tone; copyrighted media is neither included nor downloaded.

```sh
python3 examples/bad_apple_player/build.py
```

Optional media that the developer has permission to process can be supplied to
the build script. Generated movie/audio data is linked as `const`; there is no
post-link address patch. Its owned framebuffer loop polls direct system controls
without resident overlays.

Output: `build/movie-player/MonochromeMoviePlayer.MBA`, linked for G1.

## MobiGo Celeste

`examples/mobigo_celeste/` adapts the `ccleste` game logic, renders a packed
128×128 framebuffer, and uses an optimized u'nSP scaler plus system DMA.

```sh
python3 examples/mobigo_celeste/build.py
```

Output: `build/celeste/MobiGoCeleste.MBA`, linked for G1.

Controls:

| Action | Console control | Keyboard alternative |
| --- | --- | --- |
| Move | large D-pad | W/A/S/D and keyboard-arrow cells |
| Jump/start | Primary or Enter | E |
| Dash | Help or Brightness | X or Space |

Celeste polls `direct_controls.h`, so Brightness keeps its setting behavior
while also triggering dash; Volume and Off also work. Direct framebuffer
ownership means resident overlays are unavailable.

Celeste Classic, `ccleste`, and their assets remain subject to their respective
owners' terms and are not relicensed by the SDK.

## Build all complete projects

```sh
make samples
```

This verifies that all maintained complete projects still compile/package. It
does not change the canonical new-project target.

Boot and exercise every complete project through real firmware with:

```sh
make sample-emulator-check
```

That deterministic gate navigates the retail menu for the two G1 projects,
injects representative controls, checks changing framebuffer captures and
payload progress, verifies Color Cycle's Off path, and proves that the transient
overlay did not modify the base NAND.
