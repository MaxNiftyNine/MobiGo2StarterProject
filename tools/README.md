# Maintained tools

- `mobigo.py` — canonical doctor/build/run/test interface driven by
  `mobigo.project.json`.
- `build/` — target compilation, MBA packaging, and native/web emulator builds.
- `assets/` — original graphics, font, settings UI, and audio generators.
- `nand/` — firmware assembly and disposable NAND filesystem editing.
- `usb/` — guarded macOS/Windows physical-device transport.
- `verify/` — deterministic firmware/emulator integration checks.
- `docs/` — documentation link, policy, configuration, and strict-build check.
- `re/` — reproducible metadata-only reverse-engineering reports.
- `ghidra/` — MBA/GAM loader and analysis helpers.

Routine automation should begin with `python3 tools/mobigo.py`. Use a specialist
tool to diagnose or extend one pipeline stage, not to create a competing
default. Generated output belongs under `build/`.
