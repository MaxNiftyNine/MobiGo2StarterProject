# Unified `mobigo.py` command

`tools/mobigo.py` is the canonical cross-platform entry point. It reads
`mobigo.project.json` from the repository root and invokes the maintained
specialist tools with consistent target and path choices.

## Project manifest

The manifest is JSON and references `schema/mobigo-project.schema.json` for
editor completion and validation:

```json
{
  "$schema": "schema/mobigo-project.schema.json",
  "name": "MobiGo2Starter",
  "source": "app/main.c",
  "target": "system",
  "system_ui": true,
  "clean_font": false,
  "extra_sources": [],
  "homebrew": {
    "title": "My Homebrew"
  },
  "menu_icon": "assets/menu_icon.ppm"
}
```

| Field | Meaning |
| --- | --- |
| `name` | C-style identifier and output basename, at most 48 characters |
| `source` | project-relative C entry source |
| `target` | `system` for canonical SY; `game1` only for explicit legacy G1 |
| `system_ui` | generate/link the clean standard UI resources |
| `clean_font` | generate/link the clean ASCII font |
| `extra_sources` | project-relative C or u'nSP assembly sources |
| `menu_icon` | project-relative P6 PPM image; magenta is transparent; fitted and baked automatically |
| `menu_tile` | advanced raw 3,328-byte indexed launcher tile alternative |
| `palette` | advanced raw 32-byte RGB555 launcher palette alternative |
| `homebrew` | launcher display title written to the companion `.HBI` |

Unknown fields, absolute paths, paths escaping the project root, invalid names,
and missing configured files are rejected.

## `doctor`

```sh
python3 tools/mobigo.py doctor
python3 tools/mobigo.py doctor --json
```

Checks Python, manifest validity, firmware size/hashes, target compiler tools,
Wine/Winepath on Unix hosts, emulator source-build prerequisites, and any
existing host emulator build. JSON output is suitable for editors and CI
diagnosis. `MOBIGO_EMULATOR` may name a standalone release executable.

## `build`

```sh
python3 tools/mobigo.py build
python3 tools/mobigo.py build --nand
```

The first command builds the configured MBA. `--nand` also assembles the source
NAND when needed and writes a verified edited copy to
`build/nand.edited.bin`.

Every build also writes `build/<name>.HBI`. Keep that small JSON companion next
to the `.MBA` when sharing it. Homebrew Manager imports its title into the
launcher catalog. The displayed icon comes from `menu_icon`, which the build
automatically fits to 64×104, quantizes to 15 colors plus transparency, and
writes into the executable's standard menu-art header fields. Replace
`assets/menu_icon.ppm` with any P6 PPM image to choose the icon. Use solid
magenta (`#ff00ff`) for transparent pixels.
The `.MBA` remains the executable and keeps its filename.

The low-level builder keeps a content-addressed cache of repository SDK
objects under `build/cache/sdk-objects-v1`. Application, extra, and generated
sources are always rebuilt. Cache keys cover source and transitive headers,
the exact compiler/assembler binaries and flags, include arguments, and the
host runner; restored objects are hash-checked. Use
`tools/build/build_sdk_app.py --no-sdk-cache` for a deliberate cold build, or
set `MOBIGO_SDK_CACHE_DIR` to move the cache.

An explicit legacy override exists for diagnostics:

```sh
python3 tools/mobigo.py build --target game1
```

Do not make that override the default in a new project.

## `run`

```sh
python3 tools/mobigo.py run
python3 tools/mobigo.py run --mode accurate
python3 tools/mobigo.py run --mode fast --no-audio
```

Current emulator builds use role-aware transient MBA loading and open the window
when the selected application is reached. Older distributed builds fall back
to a copied NAND without cross-installing SY into G1.

- `accurate` preserves real-time pacing and recent diagnostic history unless
  explicitly changed.
- `fast` removes the real-time cap and unnecessary history bookkeeping. It
  does not change guest input mappings or peripheral execution.

In both modes, arrows drive only the D-pad; Home, End, Page Up, and Page Down
drive motion. Both modes use the same CPU and peripheral implementation.
“Accurate” does not claim that every unknown physical register is modeled.

Use `--no-build` only when the configured output already exists and is current.
The command validates the artifact's complete SY/G1 launch profile against the
manifest, so a cross-target MBA is rejected before emulation. It does not infer
same-profile source freshness; rebuild unless you independently know the output
matches the current sources.

## `test`

```sh
python3 tools/mobigo.py test
python3 tools/mobigo.py test --full
```

The normal command runs host tests, USB tests, a target-compiler check, emulator
unit tests, and emulator device/integration checks. `--full` adds every firmware
integration check, all sample builds, and complete-sample runtime checks.
Missing optional host prerequisites are reported with an actionable diagnostic.

On stock Windows without Make, the normal command runs an explicitly labeled
baseline: Python/USB tests, the complete u'nSP target-object check, the configured
project build, and the automatic-controls firmware/emulator integration. Host-C
tests and Emulator2 CTests require the Make/MSYS2 development setup. `--full`
fails instead of returning a partial success when those prerequisites are absent.

## When to use specialist tools

Use a script under `tools/build`, `tools/assets`, `tools/nand`, or `tools/verify`
when diagnosing that stage or authoring a custom project pipeline. Routine
documentation and automation should begin with `mobigo.py`.
