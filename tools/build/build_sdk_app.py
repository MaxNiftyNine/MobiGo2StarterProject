#!/usr/bin/env python3
"""Build a MobiGo 2 SDK application and package it as a complete MBA.

The builder compiles a user-provided C entrypoint together with the portable
SDK/runtime adapters and, by default, the generated common system-UI bundle.
It uses the bundled Generalplus u'nSP compiler, assembler, linker, and linker
body. On Windows those tools run natively; on macOS and Linux they run through
Wine. The resulting G1 or SY MBA is created from scratch and never copies a
retail application body.

The direct-MBA handoff enters ``main`` without a normal C CRT initialized-data
copy. Keep mutable application state in explicitly chosen title RAM or
initialize it yourself at runtime; generated system-UI assets already use the
verified const-template + writable-bundle-copy model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PureWindowsPath


SLOT_PROFILES = {
    "G1": {
        "program_base": 0x0E1A55,
        "body": "MobiGo2StarterG1.bdy",
    },
    "SY": {
        "program_base": 0x0DFC1D,
        "body": "MobiGo2StarterSY.bdy",
    },
}

CORE_SOURCES = (
    "system_controls.c",
    "hardware.c",
    "direct_controls.c",
    "input.c",
    "audio.c",
    "audio_resources.c",
    "resident_backend.c",
    "resident_input.c",
    "resident_keys.c",
    "resident_runtime.c",
    "resident_audio.c",
    "resource_bundle.c",
    "resource_graphics.c",
    "ui_family_b.c",
    "ui_family_b_animation.c",
    "settings_overlay.c",
    "resident_resources.c",
    "resident_storage.c",
    "touch.c",
    "resident_touch.c",
    "application.c",
)

# Only repository-owned SDK sources are eligible for this cache. The project
# entrypoint, extra, and generated sources compile on every invocation.
SDK_OBJECT_CACHE_VERSION = 1
C_COMPILE_FLAGS = (
    "-S",
    "-O2",
    "-ffast-math",
    "-fomit-frame-pointer",
    "-funsigned-char",
    "-Wall",
    "-mglobal-var-iram",
    "-mISA=2.0",
)
ASSEMBLER_FLAGS = ("-t4", "-sr", "-wpop")
_INCLUDE_DIRECTIVE = re.compile(r"^\s*#\s*include\s+(.+?)\s*$", re.MULTILINE)
_QUOTED_INCLUDE = re.compile(r'^"([^"]+)"$')
_ANGLE_INCLUDE = re.compile(r"^<([^>]+)>$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_is_within(path: Path, roots: tuple[Path, ...]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            pass
    return False


def discover_sdk_dependencies(
    source: Path,
    *,
    include_roots: tuple[Path, ...],
    allowed_roots: tuple[Path, ...],
) -> tuple[Path, ...] | None:
    """Return conservative local dependencies or ``None`` if cache-unsafe.

    Every literal include is followed transitively. A macro include, missing
    include, or include outside the SDK source/header roots disables caching
    for that object. This lets cacheable SDK objects compile with only the SDK
    include directory, so project headers cannot silently affect them.
    """

    include_roots = tuple(path.resolve() for path in include_roots)
    allowed_roots = tuple(path.resolve() for path in allowed_roots)
    pending = [source.resolve()]
    dependencies: set[Path] = set()

    while pending:
        current = pending.pop()
        if current in dependencies:
            continue
        if not current.is_file() or not _path_is_within(current, allowed_roots):
            return None
        dependencies.add(current)
        try:
            text = current.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        # Includes inside comments are not compiler dependencies. Stripping
        # comments also avoids disabling the cache because of documentation
        # examples in headers.
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        text = re.sub(r"//[^\r\n]*", "", text)
        for match in _INCLUDE_DIRECTIVE.finditer(text):
            operand = match.group(1).strip()
            quoted = _QUOTED_INCLUDE.fullmatch(operand)
            angled = _ANGLE_INCLUDE.fullmatch(operand)
            if quoted is None and angled is None:
                return None
            opener = '"' if quoted is not None else "<"
            name = (quoted or angled).group(1)
            search_roots = (
                (current.parent, *include_roots)
                if opener == '"'
                else include_roots
            )
            resolved = None
            for directory in search_roots:
                candidate = (directory / name).resolve()
                if candidate.is_file():
                    resolved = candidate
                    break
            if resolved is None or not _path_is_within(resolved, allowed_roots):
                return None
            pending.append(resolved)

    return tuple(sorted(dependencies, key=lambda path: path.as_posix()))


def cacheable_sdk_dependencies(
    source: Path,
    *,
    sdk_sources: set[Path],
    include_root: Path,
    source_root: Path,
) -> tuple[Path, ...] | None:
    """Gate dependency discovery to the builder's explicit SDK source set."""

    source = source.resolve()
    if source not in {path.resolve() for path in sdk_sources}:
        return None
    return discover_sdk_dependencies(
        source,
        include_roots=(include_root,),
        allowed_roots=(source_root.resolve(), include_root.resolve()),
    )


def sdk_cache_context_digest(
    *,
    compiler: Path,
    assembler: Path,
    include_root: Path,
    compiler_flags: tuple[str, ...],
    assembler_flags: tuple[str, ...],
    runner_identity: str,
) -> str:
    """Hash all build-global inputs that can affect an SDK object."""

    context = {
        "version": SDK_OBJECT_CACHE_VERSION,
        "compiler_sha256": _sha256_file(compiler),
        "assembler_sha256": _sha256_file(assembler),
        "include_root": str(include_root.resolve()),
        "compiler_flags": list(compiler_flags),
        "assembler_flags": list(assembler_flags),
        "runner": runner_identity,
    }
    encoded = json.dumps(
        context, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sdk_object_cache_key(
    source: Path,
    dependencies: tuple[Path, ...],
    *,
    root: Path,
    stem: str,
    context_digest: str,
    source_argument: str,
    include_arguments: tuple[str, ...],
) -> str:
    """Create a content-addressed key for one SDK source object."""

    digest = hashlib.sha256()
    metadata = {
        "version": SDK_OBJECT_CACHE_VERSION,
        "context": context_digest,
        "source": str(source.resolve()),
        "source_argument": source_argument,
        "stem": stem,
        "include_arguments": list(include_arguments),
    }
    digest.update(
        json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    root = root.resolve()
    for dependency in dependencies:
        dependency = dependency.resolve()
        try:
            label = dependency.relative_to(root).as_posix()
        except ValueError:
            label = dependency.as_posix()
        digest.update(b"\0path\0")
        digest.update(label.encode("utf-8"))
        digest.update(b"\0sha256\0")
        digest.update(_sha256_file(dependency).encode("ascii"))
    return digest.hexdigest()


def _cache_entry(cache_root: Path, key: str) -> Path:
    return cache_root / key[:2] / key


def _valid_cache_entry(entry: Path, key: str) -> bool:
    try:
        manifest = json.loads((entry / "manifest.json").read_text(encoding="utf-8"))
        assembly = entry / "source.asm"
        object_file = entry / "object.obj"
        return (
            manifest.get("version") == SDK_OBJECT_CACHE_VERSION
            and manifest.get("key") == key
            and assembly.is_file()
            and object_file.is_file()
            and manifest.get("assembly_sha256") == _sha256_file(assembly)
            and manifest.get("object_sha256") == _sha256_file(object_file)
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.name}.tmp-{os.getpid()}-{time.time_ns()}"
    )
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def restore_sdk_object(
    cache_root: Path,
    key: str,
    *,
    assembly_output: Path,
    object_output: Path,
) -> bool:
    """Validate and atomically restore an SDK object cache entry."""

    entry = _cache_entry(cache_root, key)
    if not _valid_cache_entry(entry, key):
        return False
    try:
        _atomic_copy(entry / "source.asm", assembly_output)
        _atomic_copy(entry / "object.obj", object_output)
    except OSError:
        return False
    return True


def store_sdk_object(
    cache_root: Path,
    key: str,
    *,
    assembly_output: Path,
    object_output: Path,
) -> None:
    """Publish a complete cache entry with an atomic directory rename."""

    entry = _cache_entry(cache_root, key)
    parent = entry.parent
    temporary = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        if _valid_cache_entry(entry, key):
            return
        temporary = Path(tempfile.mkdtemp(prefix=f".{key}.tmp-", dir=parent))
        assembly = temporary / "source.asm"
        object_file = temporary / "object.obj"
        shutil.copyfile(assembly_output, assembly)
        shutil.copyfile(object_output, object_file)
        manifest = {
            "version": SDK_OBJECT_CACHE_VERSION,
            "key": key,
            "assembly_sha256": _sha256_file(assembly),
            "object_sha256": _sha256_file(object_file),
        }
        (temporary / "manifest.json").write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        try:
            os.replace(temporary, entry)
            temporary = None
        except OSError:
            # Another build may have published the same content-addressed
            # entry. Keep its valid result and discard ours.
            if _valid_cache_entry(entry, key):
                return
            quarantine = entry.with_name(
                f".{entry.name}.invalid-{os.getpid()}-{time.time_ns()}"
            )
            try:
                os.replace(entry, quarantine)
                os.replace(temporary, entry)
                temporary = None
            except OSError:
                # Cache publication is an optimization. A race or unwritable
                # cache must never turn a successful target build into a fail.
                pass
            finally:
                shutil.rmtree(quarantine, ignore_errors=True)
    except OSError:
        # An unavailable cache must never turn a successful target build into
        # a failure. The just-built object remains in the output directory.
        return
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"build_sdk_app: {message}")


def run(command: list[str], *, env: dict[str, str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, env=env, cwd=cwd, check=False)
    if result.returncode:
        fail(f"command failed ({result.returncode}): {command[0]}")


def wine_paths(winepath: str, env: dict[str, str], paths: list[Path]) -> list[str]:
    for attempt in range(3):
        result = subprocess.run(
            [winepath, "-w", *(str(path) for path in paths)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if result.returncode == 0 and len(lines) == len(paths):
            return lines
        if attempt < 2:
            time.sleep(1)
    fail("winepath could not translate homebrew build paths")


def safe_project_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not cleaned:
        cleaned = "Homebrew"
    if cleaned[0].isdigit():
        cleaned = "HB_" + cleaned
    return cleaned[:48]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="C source containing main()")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--slot", choices=tuple(SLOT_PROFILES), default="SY")
    parser.add_argument("--name", default="HomebrewApp", help="link/output project name")
    parser.add_argument(
        "--without-system-ui",
        action="store_true",
        help="do not generate/link the common brightness/volume/off bundle",
    )
    parser.add_argument(
        "--with-clean-font",
        action="store_true",
        help="generate/link the clean-room dynamic ASCII font bundle",
    )
    parser.add_argument(
        "--extra-source",
        action="append",
        default=[],
        type=Path,
        help=(
            "additional C or u'nSP assembly source to compile/link; may be "
            "repeated. Each extra source parent is added to the include path."
        ),
    )
    parser.add_argument(
        "--install-nand",
        action="store_true",
        help="also install the MBA into a copied stitched NAND image",
    )
    parser.add_argument(
        "--nand-output",
        type=Path,
        help="output path for --install-nand (default: OUTPUT_DIR/nand.NAME.bin)",
    )
    parser.add_argument(
        "--menu-tile",
        type=Path,
        help="optional raw 0xd00-byte 64x104 indexed 4-bpp launcher tile",
    )
    parser.add_argument(
        "--palette",
        type=Path,
        help="optional raw 0x20-byte launcher RGB555 palette",
    )
    parser.add_argument(
        "--no-sdk-cache",
        action="store_true",
        help="compile SDK objects instead of using the shared content cache",
    )
    parser.add_argument(
        "--sdk-cache-dir",
        type=Path,
        help=(
            "shared SDK object cache directory "
            "(default: build/cache/sdk-objects-v1)"
        ),
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    source = args.source.expanduser().resolve()
    extra_sources = [path.expanduser().resolve() for path in args.extra_source]
    build = args.output_dir.expanduser().resolve()
    project = safe_project_name(args.name)
    profile = SLOT_PROFILES[args.slot]
    program_base = int(profile["program_base"])

    ide = root / "vendor" / "generalplus" / "compiler" / "windows" / "unSPIDE_4.1.1"
    toolchain = ide / "toolchain"
    library = ide / "library" / "CMacro" / "CMacro1232.lib"
    body = root / "vendor" / "generalplus" / "linker" / str(profile["body"])
    include = root / "include"
    generated = build / "generated"
    generated_font = build / "generated_font"

    if not source.is_file():
        fail(f"source does not exist: {source}")
    for extra_source in extra_sources:
        if not extra_source.is_file():
            fail(f"extra source does not exist: {extra_source}")
    if len({source, *extra_sources}) != 1 + len(extra_sources):
        fail("source files must be unique")
    build.mkdir(parents=True, exist_ok=True)

    sdk_sources = [root / "src" / name for name in CORE_SOURCES]
    sources = list(sdk_sources)
    if not args.without_system_ui:
        subprocess.run(
            [
                sys.executable,
                str(root / "tools" / "assets" / "build_system_ui_bundle.py"),
                str(generated),
                "--prefix",
                "mobigo_clean_system_ui",
            ],
            check=True,
        )
        standard_controls = root / "src" / "standard_controls.c"
        sdk_sources.append(standard_controls)
        sources.append(standard_controls)
        sources.append(generated / "mobigo_clean_system_ui_resources.c")
    if args.with_clean_font:
        subprocess.run(
            [
                sys.executable,
                str(root / "tools" / "assets" / "build_clean_font_bundle.py"),
                str(generated_font),
                "--prefix",
                "mobigo_clean_font",
            ],
            check=True,
        )
        sources.append(generated_font / "mobigo_clean_font_resources.c")
    sources.extend(extra_sources)
    sources.append(source)
    extra_include_dirs = list(
        dict.fromkeys([source.parent, *(path.parent for path in extra_sources)])
    )

    native_windows = os.name == "nt"
    wine = None if native_windows else (
        os.environ.get("MOBIGO_WINE") or shutil.which("wine")
    )
    winepath = None if native_windows else shutil.which("winepath")
    if not native_windows and (not wine or not winepath):
        fail("Wine and winepath are required on macOS and Linux")

    required = [
        toolchain / "udocc.exe",
        toolchain / "xasm16.exe",
        toolchain / "xlink16.exe",
        library,
        body,
        include,
        *extra_include_dirs,
        *sources,
    ]
    if not args.without_system_ui:
        required.append(generated / "mobigo_clean_system_ui_resources.h")
    if args.with_clean_font:
        required.append(generated_font / "mobigo_clean_font_resources.h")
    for optional in (args.menu_tile, args.palette):
        if optional is not None:
            required.append(optional.expanduser().resolve())
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        fail("required path is missing: " + missing[0])

    env = os.environ.copy()
    env.setdefault("WINEDEBUG", "-all")
    env.setdefault("MVK_CONFIG_LOG_LEVEL", "0")

    cache_disabled_by_env = os.environ.get(
        "MOBIGO_DISABLE_SDK_CACHE", ""
    ).strip().lower() in {"1", "true", "yes", "on"}
    cache_enabled = not args.no_sdk_cache and not cache_disabled_by_env
    cache_root = (
        args.sdk_cache_dir.expanduser().resolve()
        if args.sdk_cache_dir is not None
        else Path(
            os.environ.get(
                "MOBIGO_SDK_CACHE_DIR",
                str(root / "build" / "cache" / "sdk-objects-v1"),
            )
        ).expanduser().resolve()
    )

    requested = [root, ide, toolchain, library, body, include, build]
    if not args.without_system_ui:
        requested.append(generated)
    if args.with_clean_font:
        requested.append(generated_font)
    requested.extend(extra_include_dirs)
    requested.extend(sources)
    translated = (
        [str(path) for path in requested]
        if native_windows
        else wine_paths(str(winepath), env, requested)
    )
    index = 0
    root_w = translated[index]; index += 1
    ide_w = translated[index]; index += 1
    toolchain_w = translated[index]; index += 1
    library_w = translated[index]; index += 1
    body_w = translated[index]; index += 1
    include_w = translated[index]; index += 1
    build_w = translated[index]; index += 1
    generated_w = None
    if not args.without_system_ui:
        generated_w = translated[index]; index += 1
    generated_font_w = None
    if args.with_clean_font:
        generated_font_w = translated[index]; index += 1
    extra_include_w = translated[index : index + len(extra_include_dirs)]
    index += len(extra_include_dirs)
    sources_w = translated[index:]
    if native_windows:
        env["PATH"] = str(toolchain) + os.pathsep + env.get("PATH", "")
    else:
        env["WINEPATH"] = toolchain_w + (
            ";" + env["WINEPATH"] if env.get("WINEPATH") else ""
        )

    runner_identity = "native-windows"
    if not native_windows:
        wine_version = subprocess.run(
            [str(wine), "--version"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        version_text = (wine_version.stdout or wine_version.stderr).strip()
        runner_identity = f"wine:{version_text or 'unknown'}"
    cache_context = None
    if cache_enabled:
        cache_context = sdk_cache_context_digest(
            compiler=toolchain / "udocc.exe",
            assembler=toolchain / "xasm16.exe",
            include_root=include,
            compiler_flags=C_COMPILE_FLAGS,
            assembler_flags=ASSEMBLER_FLAGS,
            runner_identity=runner_identity,
        )

    def tool_command(executable: Path, *arguments: str) -> list[str]:
        if native_windows:
            return [str(executable), *arguments]
        return [str(wine), str(executable), *arguments]

    object_paths: list[str] = []
    used_stems: dict[str, int] = {}
    sdk_source_set = {path.resolve() for path in sdk_sources}
    cache_hits = 0
    cache_misses = 0
    for source_path, source_w in zip(sources, sources_w):
        stem = source_path.stem
        count = used_stems.get(stem, 0)
        used_stems[stem] = count + 1
        if count:
            stem = f"{stem}_{count}"
        asm_w = f"{build_w}\\{stem}.asm"
        obj_w = f"{build_w}\\{stem}.obj"
        asm_path = build / f"{stem}.asm"
        obj_path = build / f"{stem}.obj"
        object_paths.append(obj_w)
        include_args = [f"-I{include_w}"]
        if generated_w is not None:
            include_args.append(f"-I{generated_w}")
        if generated_font_w is not None:
            include_args.append(f"-I{generated_font_w}")
        include_args.extend(f"-I{directory}" for directory in extra_include_w)
        if source_path.suffix.lower() == ".c":
            cache_key = None
            if cache_context is not None and source_path.resolve() in sdk_source_set:
                dependencies = cacheable_sdk_dependencies(
                    source_path,
                    sdk_sources=sdk_source_set,
                    include_root=include,
                    source_root=root / "src",
                )
                if dependencies is not None:
                    # A verified SDK-only dependency graph deliberately omits
                    # project/generated include paths. This makes entries
                    # reusable across independent application output trees.
                    include_args = [f"-I{include_w}"]
                    cache_key = sdk_object_cache_key(
                        source_path,
                        dependencies,
                        root=root,
                        stem=stem,
                        context_digest=cache_context,
                        source_argument=source_w,
                        include_arguments=tuple(include_args),
                    )
                    if restore_sdk_object(
                        cache_root,
                        cache_key,
                        assembly_output=asm_path,
                        object_output=obj_path,
                    ):
                        cache_hits += 1
                        print(f"[u'nSP CACHE HIT] {source_path.name}")
                        continue
                    cache_misses += 1
                    print(f"[u'nSP CACHE MISS] {source_path.name}")
            print(f"[u'nSP C] {source_path.name}")
            run(
                tool_command(
                    toolchain / "udocc.exe",
                    *C_COMPILE_FLAGS,
                    *include_args,
                    "-o",
                    asm_w,
                    source_w,
                ),
                env=env,
            )
            assembler_input = asm_w
        elif source_path.suffix.lower() in (".asm", ".s"):
            assembler_input = source_w
        else:
            fail(f"unsupported source type: {source_path}")
        print(f"[u'nSP ASM] {source_path.name}")
        run(
            tool_command(
                toolchain / "xasm16.exe",
                *ASSEMBLER_FLAGS,
                *include_args,
                "-o",
                obj_w,
                assembler_input,
            ),
            env=env,
        )
        if source_path.suffix.lower() == ".c" and cache_key is not None:
            store_sdk_object(
                cache_root,
                cache_key,
                assembly_output=asm_path,
                object_output=obj_path,
            )

    ary = build / f"{project}.ary"
    # The resident graphics path expects generated resource data to retain the
    # Generalplus linker's section alignment even as applications add sources.
    # Align both executable and initialized-data sections for every object.
    ary_lines = [
        *(f'Obj: "{obj}"' for obj in object_paths),
        *(f'Align: CODE in "{PureWindowsPath(obj).name}" with 4'
          for obj in object_paths),
        *(f'Align: NB_DATA in "{PureWindowsPath(obj).name}" with 4'
          for obj in object_paths),
        f'Lib: "{library_w}"',
        f'PrjPath: "{root_w}\\"',
        f'LibPath: "{ide_w}\\"',
        f'LibPath: "{ide_w}\\library\\CMacro"',
        'IDE_Version: "4.1.1"',
        "",
    ]
    ary.write_text("\n".join(ary_lines), encoding="ascii")

    app_s37 = build / f"{project}.s37"
    print(f"[u'nSP LINK] {app_s37.name}")
    run(
        tool_command(
            toolchain / "xlink16.exe",
            "-as",
            f"{build_w}\\{project}.ary",
            f"{build_w}\\{project}.s37",
            "-initdata",
            "-body",
            "GPL16250VA_CS0SRAM",
            "-nobdy",
            "-bfile",
            body_w,
            "-undefined-opt",
            "__TgP190708CM",
            "-undefined-opt",
            "__TgP190708CL",
            "-undefined-opt",
            "__TgP190708M",
        ),
        env=env,
        cwd=build,
    )

    root_lik = root / f"{project}.lik"
    if root_lik.is_file():
        root_lik.replace(build / root_lik.name)

    linker_map = build / f"{project}.map"
    if not linker_map.exists():
        alternatives = list(build.glob("*.map"))
        if len(alternatives) != 1:
            fail("could not identify linker map")
        linker_map = alternatives[0]

    match = re.search(
        r"^_main\s+([0-9A-Fa-f]+)",
        linker_map.read_text(errors="replace"),
        re.MULTILINE,
    )
    if not match:
        fail("could not find _main in linker map")
    main_address = int(match.group(1), 16)

    app_bin = build / "app.bin"
    vector_start = program_base + 0xFFF0
    run(
        [
            sys.executable,
            str(root / "tools" / "build" / "srec_to_bin.py"),
            str(app_s37),
            str(app_bin),
            hex(program_base),
            hex(vector_start),
        ],
        env=env,
    )
    program = bytearray(app_bin.read_bytes())
    if len(program) < 4:
        fail("compiler produced an unexpectedly small payload")
    struct.pack_into(
        "<HH",
        program,
        0,
        0xFE80 | ((main_address >> 16) & 0x3F),
        main_address & 0xFFFF,
    )
    app_bin.write_bytes(program)

    mba = build / f"{project}.MBA"
    mba_command = [
        sys.executable,
        str(root / "tools" / "build" / "build_mba.py"),
        "--slot",
        args.slot,
        "--payload",
        str(app_bin),
        "--output",
        str(mba),
    ]
    if args.menu_tile is not None:
        mba_command.extend(["--menu-tile", str(args.menu_tile.expanduser().resolve())])
    if args.palette is not None:
        mba_command.extend(["--palette", str(args.palette.expanduser().resolve())])
    run(mba_command, env=env)

    nand = None
    if args.install_nand:
        source_nand = root / "vendor" / "firmware" / "nand.us-stitched.bin"
        if not source_nand.exists():
            run(
                [
                    sys.executable,
                    str(root / "tools" / "nand" / "assemble_nand.py"),
                    "--output",
                    str(source_nand),
                ],
                env=env,
            )
        nand = (
            args.nand_output.expanduser().resolve()
            if args.nand_output is not None
            else build / f"nand.{project}.bin"
        )
        nand.parent.mkdir(parents=True, exist_ok=True)
        run(
            [
                sys.executable,
                str(root / "tools" / "nand" / "install_mba.py"),
                str(source_nand),
                str(mba),
                str(nand),
                "--slot",
                args.slot,
                "--editor",
                str(root / "tools" / "nand" / "nandfs.py"),
            ],
            env=env,
        )

    (build / "entry.txt").write_text(f"0x{program_base:X}\n", encoding="ascii")
    summary = (
        f"PASS slot={args.slot} main=0x{main_address:X} "
        f"payload_bytes={len(program)} mba={mba}"
    )
    if nand is not None:
        summary += f" nand={nand}"
    if cache_enabled:
        summary += (
            f" sdk_cache_hits={cache_hits} sdk_cache_misses={cache_misses}"
        )
    else:
        summary += " sdk_cache=disabled"
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
