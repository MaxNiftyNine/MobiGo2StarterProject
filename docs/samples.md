# Sample projects

The maintained examples use the same SDK builder and from-scratch MBA packer as
the starter application. No sample needs a donor MBA, private linker body, old
S-record converter, or PowerShell-only wrapper.

## Color Cycle

[`examples/color_cycle`](https://github.com/MaxNiftyNine/MobiGo2StarterProject/tree/main/examples/color_cycle)
is the smallest low-level G1 display example. It reads the launcher's active
framebuffer, fills it through system DMA, preserves interrupt servicing, and
keeps the watchdog alive.

```sh
python3 examples/color_cycle/build.py
```

## Monochrome movie player

[`examples/bad_apple_player`](https://github.com/MaxNiftyNine/MobiGo2StarterProject/tree/main/examples/bad_apple_player)
ports the Bad Apple proof-of-concept player without including copyrighted
media. Its default build generates an original moving-box clip and tone. You
can optionally provide media you have permission to use:

```sh
python3 -m pip install imageio-ffmpeg
python3 examples/bad_apple_player/build.py \
  --video path/to/video.mp4 --audio path/to/audio.wav
```

Video is encoded as 64x48 monochrome XOR deltas with word-run compression;
audio is unsigned 8-bit PCM. Both become linked const resources, so there are
no patched addresses or post-link binary append step.

## MobiGo Celeste

[`examples/mobigo_celeste`](https://github.com/MaxNiftyNine/MobiGo2StarterProject/tree/main/examples/mobigo_celeste)
is the large, advanced sample. It adapts the `ccleste` game logic, packs four
PICO-8 pixels per word, and uses a hand-tuned u'nSP row scaler with system DMA.

```sh
python3 examples/mobigo_celeste/build.py
```

The D-pad moves, the primary button jumps or starts, and Help or Brightness
dashes. Celeste and upstream assets are not covered by this project's MIT
license; review the sample README and upstream rights before redistribution.

Add `--install-nand` to any individual command to create a copied NAND with the
MBA installed in the G1 slot. Build all three projects with `make samples`.
