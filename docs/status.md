# Project status

## Finished

- Clean-room public headers and C implementations for the recovered common
  runtime surfaces.
- Original system-control UI and font generators.
- Graphics bundles, UI objects, animation, touch, input, storage, and audio
  resource support.
- From-scratch G1/SY MBA packaging, launcher art, NAND installation, and USB
  tooling.
- Host tests and end-to-end emulator verification scripts.
- MBA/GAM Ghidra loader and naming helpers.
- Cross-platform starter build: native Generalplus tools on Windows and Wine on
  macOS/Linux.

## Still open

- Broader physical-hardware validation of shutdown, asynchronous relaunch, and
  audio state/control details. The default title-RAM arena, graphics/input, and
  homebrew audio output have now been exercised on a real console.
- More high-level drawing, scene, text-layout, and game-framework conveniences.
- Automatic conversion for more common art and music authoring formats.
- Additional retail-title comparison to distinguish universal SDK behavior
  from version- or title-specific behavior.

`project-status.md` is the detailed evidence ledger, including exact emulator
checks and per-subsystem limitations.
