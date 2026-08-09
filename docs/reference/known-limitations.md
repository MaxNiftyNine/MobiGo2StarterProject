# Known limitations

These limits define where a port should choose a conservative design or add a
targeted experiment. The [capability matrix](../testing/capability-matrix.md)
is the authoritative implementation-status ledger.

## Emulator fidelity

- D-pad and motion are separate in both modes. Accurate mode adds default
  real-time pacing and diagnostic history, but it is not a cycle-perfect or
  electrical simulation.
- Analog SPU output, uncommon envelopes, ADPCM36 edge cases, rare PPU
  transforms, and several timer selectors are only partially modeled.
- A passing emulator run cannot validate USB electrical behavior, LCD analog
  timing, speaker output quality, touch calibration, or all hardware revisions.

## Storage

- The Manager's fresh-file publication, `/HB` creation/rediscovery, and empty
  directory removal are verified on one US retail unit. Other firmware regions
  and hardware revisions remain less certain than packed existing-file access.
- Homebrew Manager refuses to replace SY unless `/HB` is observable after
  creation and its recovery file and catalog both read back exactly. Complete
  uninstall restores and verifies the original SY before deleting `/HB`.
- All destructive tests belong on disposable copied NAND. Keep an untouched
  source image and physical-console recovery backup.

## Runtime and memory

- MBA entry does not provide a conventional initialized-data CRT contract.
  Explicitly initialize mutable state and place it in the documented title-RAM
  arena.
- Resident fixed-address services are reconstructed interfaces. Unlisted
  entry points and guessed prototypes are unsupported.
- Direct framebuffer ownership bypasses resident rendering. Code using it must
  service the watchdog and cannot expect resident UI overlays to render.

## Hardware coverage

- Touch calibration and accelerometer device/revision variants have not been
  surveyed across all consoles.
- Shutdown and asynchronous relaunch behavior have bounded physical evidence;
  treat both as terminal transitions and avoid post-call assumptions. The
  target hardware suite recognizes only its two bundled/verified region
  fixtures because no resident directory-enumeration/current-path API is known.
- DMA/framebuffer helpers cover the common inherited-buffer workflow. Raw MMIO
  and undocumented controller modes remain private research surfaces.

## Formats and assets

- The SDK implements the MBA/GAM, resource, graphics, and audio subsets needed
  by current examples; unusual retail descriptor fields may be unresolved.
- Sequenced music and ADPCM36 support are compatible subsets, not general
  converters for every retail asset.
- Vendor firmware/toolchain files have separate redistribution terms.

When a port depends on an item above, isolate it behind a small interface, add
an emulator regression, and include a guided hardware check rather than
spreading the assumption throughout the game.
