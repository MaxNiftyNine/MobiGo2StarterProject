# MobiGo 2 Bad Apple POC

This project builds a self-contained little-endian unSP payload for the MobiGo
2 G1 MBA slot. The first 500 video frames are stored at 64x48 monochrome and
10 FPS using XOR delta plus word-run compression. The player expands each frame
to five 320-pixel RGB565 scanlines at a time and loops forever.

No copyrighted media is included or downloaded. Put a video you have permission
to use at `assets/source.mp4`. With ffmpeg installed, generate the compact audio
loop and then build:

```powershell
python tools\encode_audio.py assets\source.mp4 assets\badapple.pcm
powershell -ExecutionPolicy Bypass -File tools\build.ps1
```

The output `build/bad_apple.bin` is a payload, not an MBA. From the project
root, package it with:

```sh
python3 tools/build_mba.py --slot G1 \
  --payload documents/samples/bad_apple_player/build/bad_apple.bin \
  --output build/BadAppleG1.MBA
```

The player is linked at the verified G1 application entry `0x0E1A55`. Its entry
stub only jumps to `main`; it deliberately preserves the IRQ/FIQ state inherited
from LD. The resident loop services the hardware watchdog, reads the live
FBI/FBO addresses selected by the launcher, and transfers a 320-word scanline
scratch buffer at `0x6100` with the documented GPL16250VA system-DMA completion
sequence. Its 192-word delta bitmap is at `0x6000`; no compiler-managed global
data is used. It does not assume that `0x018000` is writable framebuffer RAM.
Returning from `main` is intentionally impossible because a top-level return
exits to LD.

The video path was confirmed on a physical MobiGo 2. The current audio revision
models the retail output gate and passes emulator tests, but has not yet been
confirmed audible on physical hardware.
