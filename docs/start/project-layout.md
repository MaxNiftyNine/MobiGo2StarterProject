# Project layout and sources of truth

The repository deliberately separates supported development surfaces from raw
reverse-engineering evidence.

| Path | Role | Source of truth? |
| --- | --- | --- |
| `app/` | editable starter | Yes, for the minimal application pattern |
| `include/mobigo_sdk/` | public API declarations | Yes, for signatures and contracts |
| `src/` | clean-room SDK implementation | Yes, with tests |
| `examples/` | focused probes and complete projects | Only for the feature they demonstrate |
| `tests/` | host and packaging regressions | Yes, for covered behavior |
| `emulator/` | emulator source and hardware tests | Yes for modeled behavior, not automatically physical proof |
| `tools/` | unified and specialist tools | Yes for current command behavior |
| `docs/` | current developer manual | Yes for supported workflows |
| `research/` | dated evidence, reports, and experiments | No; historical evidence only |
| `vendor/` | third-party and device-derived inputs | Inputs, not clean-room API source |
| `build/` | generated products | Never commit |

## Which document wins?

When sources disagree, use this order:

1. current public header and its tests;
2. current unified CLI behavior and validation;
3. the published manual and capability matrix;
4. a maintained complete example;
5. dated research notes;
6. archived guides and experiments.

An address or filename in a research report records an observation. It is not a
portable application constant unless the current API or reference manual says
so.

## Public versus target-only APIs

Most headers expose either portable logic or bindings that require the resident
firmware. `standard_controls.h` is the resident-lifecycle convenience layer;
`direct_controls.h` preserves settings and Off handling in an owned framebuffer
loop without resident overlays. `hardware.h` is
also target-only and intentionally low-level.

Host tests can exercise portable authoring and policy helpers. Resident and
hardware bindings must be compiled for u'nSP and validated against firmware in
the emulator or on a physical console.

The target builder accepts C99-style `.c` and u'nSP `.asm`/`.s` sources. It has
no C++ frontend or established target C++ ABI. C++20 under `emulator/` belongs
to the host emulator and is not an application-language precedent.

## Generated code

Asset tools emit deterministic C, headers, binaries, manifests, and previews.
Generated files belong under `build/` unless a maintained example intentionally
checks in a compiler-ready asset for licensing or reproducibility reasons.

## Project configuration

`mobigo.project.json` is the canonical project manifest. It references
`schema/mobigo-project.schema.json` and declares the output name, entry source,
target (`system` or legacy `game1`), standard UI/font choices, extra sources,
and optional launcher art. All paths are project-relative; absolute and escaping
paths are rejected.

See the [unified CLI reference](../tools/mobigo-cli.md) for every field.

## Documentation placement

The website holds supported concepts and reference material. Small directory
READMEs point back to it. Long chronological investigations belong under
`research/`, with a date and an explicit warning that current status lives in
the capability matrix.
