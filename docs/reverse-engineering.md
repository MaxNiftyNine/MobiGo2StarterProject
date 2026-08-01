# Reverse engineering tools

## Ghidra loader

The `tools/ghidra/loader/MobiGoMbaLoader` extension recognizes MBA and GAM variants and
creates word-addressed program memory, header/menu structures, entry points,
firmware service labels, hardware memory ranges, and known MMIO symbols.

Install [ghidra-unSP](https://github.com/20051231/ghidra-unSP), then build:

```sh
cd tools/ghidra/loader/MobiGoMbaLoader
GHIDRA_INSTALL_DIR=/path/to/ghidra gradle
```

Install the ZIP produced under `dist/` through Ghidra's extension manager. The
Java and Python helpers under `tools/ghidra/scripts` seed resident services, list
xrefs, inspect memory, and batch decompile known targets.

## Evidence archive

`research/notes/` contains subsystem-by-subsystem reconstruction notes. `research/reports/`
contains machine-readable cross-title function, asset, page-map, and audio
catalogs. These are evidence and research aids; application authors can stay
in `app/`, `include/`, `examples/`, and the public docs.

The SDK is clean-room code. Retail executable, artwork, and audio bytes are not
part of the reconstructed API or generated assets.
