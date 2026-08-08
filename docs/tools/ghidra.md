# Ghidra and reproducible research

The MBA/GAM loader extension is under
`tools/ghidra/loader/MobiGoMbaLoader/`. It recognizes the container, maps
word-addressed executable regions and compacted pages, identifies entries and
header structures, and seeds known firmware/MMIO symbols.

## Build the extension

Install Ghidra, Gradle, and
[ghidra-unSP](https://github.com/20051231/ghidra-unSP), then run:

```sh
cd tools/ghidra/loader/MobiGoMbaLoader
GHIDRA_INSTALL_DIR=/path/to/ghidra gradle
```

Install the generated ZIP through Ghidra's extension manager and restart Ghidra.

## Analysis scripts

Reusable Java and Python scripts under `tools/ghidra/scripts/` seed resident
services, list cross-references, inspect words/instructions, and decompile
selected targets.

Offline tools under `tools/re/` catalog exact shared blocks, resident calls,
resource bundles, audio resources, and MBA page maps. Their JSON outputs live in
`research/reports/`.

## Clean-room boundary

Reports may contain hashes, offsets, counts, structural metadata, and descriptive
names. Do not commit executable dumps, copied retail art/audio, decompiler
listings containing vendor code, or personal absolute source paths.

Research notes are evidence, not current workflow instructions. Promote a
confirmed result into the relevant Hardware, Software, API, and capability pages
instead of telling application developers to read a chronological log.
