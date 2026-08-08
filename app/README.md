# Editable starter application

`app/main.c` is the canonical SY starter. It uses the resident
setup/step/finalize lifecycle and `standard_controls.h`, so Volume Up, Volume
Down, Brightness, and Off work when the control object is initialized and
polled each frame.

The starter deliberately draws no game artwork, so a clean black application
screen is expected. In the emulator, press F8 (Volume Up) or F6 (Brightness) to
confirm the generated system overlay before adding your own scene.

From the repository root:

```sh
python3 tools/mobigo.py doctor
python3 tools/mobigo.py run
```

Project metadata belongs in `mobigo.project.json`; the schema is
`schema/mobigo-project.schema.json`. Use `python3 tools/mobigo.py build --nand`
only when a persistent copied-NAND artifact is required.

The MBA handoff does not perform a conventional initialized-data/BSS startup.
Keep immutable data `const`, explicitly initialize writable state, and reserve
non-overlapping title RAM for generated mutable resource graphs. See
[`docs/guides/lifecycle-memory.md`](../docs/guides/lifecycle-memory.md).
