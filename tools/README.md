# Tools

- `assets/` — original graphics, font, and audio generators.
- `build/` — SDK/MBA and emulator build entry points.
- `nand/` — NAND assembly, filesystem editing, and MBA installation.
- `usb/` — safe device-management commands and transports.
- `verify/` — end-to-end firmware/emulator regressions.
- `re/` — offline executable, asset, audio, and function analysis.
- `ghidra/` — the MBA/GAM loader and reusable analysis scripts.

User-facing launchers live in `scripts/`; build products belong only in
`build/`.
