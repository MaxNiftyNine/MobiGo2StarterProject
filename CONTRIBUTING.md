# Contributing

Contributions should keep the supported application path small, reproducible,
and safe on both Emulator2 and physical hardware.

## Source boundaries

- Application code belongs in `app/` or a maintained project under `examples/`.
- Public declarations belong in `include/mobigo_sdk/`.
- SDK implementations belong in `src/`.
- Developer utilities belong in the matching `tools/` category.
- Current user documentation belongs in `docs/`.
- Raw evidence, experiments, and superseded notes belong in `research/`.
- Generated products belong under `build/` and must not be committed.

Do not add retail game code, art, or audio to the clean-room SDK. Do not add
device firmware or third-party binaries without a documented redistribution
basis in `THIRD_PARTY.md`.

## Compatibility rules

- New applications use the SY profile by default.
- G1 is an explicit legacy target. Do not copy G1 addresses, paths, or install
  commands into general starter guidance.
- Never hard-code a regional MBA filename. Use the filesystem-aware NAND or USB
  installer to discover the existing slot file.
- Prefer resident SDK APIs when running through the resident lifecycle. Direct
  MMIO helpers belong in `hardware.h` and are intended for deliberately
  low-level ports.
- Standard volume, brightness, and Off behavior should use
  `standard_controls.h` under the resident lifecycle or `direct_controls.h`
  in a deliberate framebuffer-owned loop. Use the portable policy directly
  only for a custom backend.

## Validation

Start with:

```sh
python3 tools/mobigo.py doctor
python3 tools/mobigo.py test
```

Run the narrowest relevant emulator checks while developing and
`python3 tools/mobigo.py test --full` before submitting. Add a deterministic
regression when changing a recovered format, resident binding, hardware model,
or command-line workflow.

Documentation changes must pass:

```sh
make docs-check
```

Commands in documentation must be runnable from the repository root unless the
text explicitly changes directory. Current behavior must be stated separately
from emulator inference and unresolved hardware behavior.

## Documentation style

- Write for a developer arriving without conversation history.
- Do not mention prompts, requests, handoffs, agents, or private workspaces as
  provenance.
- Use the confidence vocabulary in `docs/reference/source-confidence.md`.
- Link to current guides rather than copying long instructions into many
  READMEs.
- When behavior changes, update the capability matrix and the related API or
  subsystem page in the same change.
