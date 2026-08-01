# Monochrome movie player

This G1 example is the SDK port of the original Bad Apple proof-of-concept. It
plays a 64x48, 1-bpp XOR-delta/RLE movie scaled to 320x240 and loops an unsigned
8-bit PCM sample through the GPL16250 SPU.

No copyrighted movie or audio is included or downloaded. A normal build uses
an original moving-box clip and tone generated locally, so the example works
from a clean checkout:

```sh
python3 examples/bad_apple_player/build.py
```

The output is `build/movie-player/MonochromeMoviePlayer.MBA`.

To encode media you have permission to use:

```sh
python3 -m pip install imageio-ffmpeg
python3 examples/bad_apple_player/build.py \
  --video path/to/video.mp4 --audio path/to/audio.wav --max-frames 300
```

The G1 executable window is about 149 KB, shared by code, movie, and audio. If
the packer reports that the payload is too large, shorten the clip with
`--max-frames` or use simpler source material. The encoder defaults to 10 FPS.

Unlike the historical build, this port links generated resources as const data
and lets the standard SDK builder discover their addresses. It no longer
appends blobs, recompiles with patched address macros, carries a private linker
body, or requires PowerShell. Add `--install-nand` to create a NAND image too.
