#!/usr/bin/env python3
"""Validate the maintained documentation without third-party Python imports."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
CONFIG = ROOT / "mkdocs.yml"
CANONICAL_SITE_URL = "https://maxniftynine.github.io/MobiGo2StarterProject/"
CANONICAL_MANIFEST_SCHEMA = "schema/mobigo-project.schema.json"

DOC_TREES = (
    "docs",
    "app",
    "emulator",
    "include",
    "src",
    "examples",
    "tools",
    "scripts",
    "vendor",
    "research",
)
ROOT_DOCS = ("README.md", "CONTRIBUTING.md", "AGENTS.md")

FORBIDDEN_PHRASES = (
    "the user's request",
    "the user asked",
    "the user wanted",
    "user requested",
    "user asked",
    "user wanted",
    "i was asked to",
    "we were asked to",
    "the prompt asked",
    "the prompt says",
    "parent agent",
    "subagent",
    "sub-agent",
    "final handoff",
    "continuation prompt",
    "prompt leak",
    "prompt leaking",
    "ai slop",
    "dumb documentation",
    "this repo is bad",
    "not really a good repo",
)

STALE_PATH_PATTERNS = (
    (re.compile(r"tools[\\/]mobigo_usb", re.IGNORECASE),
     "use tools/usb"),
    (re.compile(r"(?<!scripts[\\/])build_and_run\.(?:ps1|command|bat|sh)",
                re.IGNORECASE),
     "use tools/mobigo.py or the launcher under scripts/"),
    (re.compile(r"\b\d{5,6}(?:G1|SY)\.MBA\b", re.IGNORECASE),
     "discover the regional slot filename instead of embedding it"),
)

MARKDOWN_DESTINATION_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
NAV_DOC_RE = re.compile(r"^\s*-\s+[^:]+:\s+([^\s#]+\.md)\s*$", re.MULTILINE)
REPOSITORY_PATH_PREFIXES = (
    "app/", "docs/", "emulator/", "examples/", "include/", "research/",
    "schema/", "scripts/", "src/", "tests/", "tools/", "vendor/",
)
ROOT_PATHS = {
    "AGENTS.md", "CONTRIBUTING.md", "LICENSE", "Makefile", "README.md",
    "THIRD_PARTY.md", "mkdocs.yml", "mobigo.project.json",
}
GENERATED_REPOSITORY_PATHS = {
    "vendor/firmware/nand.us-stitched.bin": (
        "tools/nand/assemble_nand.py",
        "vendor/firmware/nand.us-stitched.bin.part00",
        "vendor/firmware/nand.us-stitched.bin.part01",
    ),
}
REQUIRED_NAV_SECTIONS = (
    "Start", "Guides", "API", "Hardware", "Software", "Tools", "Testing",
    "Examples", "Reference",
)


def maintained_markdown() -> list[Path]:
    files = [ROOT / name for name in ROOT_DOCS if (ROOT / name).is_file()]
    for dirname in DOC_TREES:
        base = ROOT / dirname
        if base.is_dir():
            files.extend(base.rglob("*.md"))
    return sorted(set(files))


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_config(errors: list[str]) -> None:
    if not CONFIG.is_file():
        errors.append("mkdocs.yml: missing")
        return

    text = CONFIG.read_text(encoding="utf-8")
    match = re.search(r"^site_url:\s*(\S+)\s*$", text, re.MULTILINE)
    if not match or match.group(1) != CANONICAL_SITE_URL:
        errors.append(
            "mkdocs.yml: site_url must be " + CANONICAL_SITE_URL
        )
    if not re.search(r"^docs_dir:\s*docs\s*$", text, re.MULTILINE):
        errors.append("mkdocs.yml: docs_dir must be docs")
    if not re.search(r"^\s*-\s+search\s*$", text, re.MULTILINE):
        errors.append("mkdocs.yml: search plugin is required")
    for section in REQUIRED_NAV_SECTIONS:
        if not re.search(rf"^\s{{2}}-\s+{re.escape(section)}:\s*$", text, re.MULTILINE):
            errors.append(f"mkdocs.yml: required navigation section is missing: {section}")

    for target in NAV_DOC_RE.findall(text):
        path = DOCS / target
        if not path.is_file():
            errors.append(f"mkdocs.yml: nav target does not exist: docs/{target}")

    manifest_path = ROOT / "mobigo.project.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"mobigo.project.json: cannot load canonical manifest: {exc}")
    else:
        if manifest.get("$schema") != CANONICAL_MANIFEST_SCHEMA:
            errors.append(
                "mobigo.project.json: $schema must be " + CANONICAL_MANIFEST_SCHEMA
            )
        if manifest.get("target") != "system":
            errors.append("mobigo.project.json: new-project default target must be system/SY")
    if not (ROOT / CANONICAL_MANIFEST_SCHEMA).is_file():
        errors.append(f"missing project schema: {CANONICAL_MANIFEST_SCHEMA}")
    for generated, prerequisites in GENERATED_REPOSITORY_PATHS.items():
        for prerequisite in prerequisites:
            if not (ROOT / prerequisite).is_file():
                errors.append(
                    f"generated documentation path {generated} has missing "
                    f"prerequisite: {prerequisite}"
                )


def strip_c_header(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    output: list[str] = []
    in_directive = False
    for line in text.splitlines():
        if in_directive or line.lstrip().startswith("#"):
            in_directive = line.rstrip().endswith("\\")
            continue
        output.append(line)
    return "\n".join(output)


def normalized_c(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def declared_prototypes(text: str) -> dict[str, str]:
    prototypes: dict[str, str] = {}
    pattern = re.compile(
        r"(?m)^[ \t]*"
        r"([A-Za-z_][^;{}#]*?\b(mg_sdk_[A-Za-z0-9_]+)\s*"
        r"\([^;{}]*?\)\s*;)",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        prototypes[match.group(2)] = normalized_c(match.group(1))
    return prototypes


def public_prototypes() -> dict[str, str]:
    prototypes: dict[str, str] = {}
    for header in (ROOT / "include" / "mobigo_sdk").glob("*.h"):
        text = strip_c_header(header.read_text(encoding="utf-8"))
        prototypes.update(declared_prototypes(text))
    return prototypes


def check_callable_coverage(errors: list[str]) -> None:
    api_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((DOCS / "api").glob("*.md"))
    )
    documented: dict[str, set[str]] = {}
    for block in re.findall(r"```c\s*\n(.*?)```", api_text, re.DOTALL):
        for name, prototype in declared_prototypes(block).items():
            documented.setdefault(name, set()).add(prototype)

    for name, prototype in sorted(public_prototypes().items()):
        candidates = documented.get(name)
        if not candidates:
            errors.append(f"docs/api: public callable has no C signature: {name}")
        elif prototype not in candidates:
            errors.append(
                f"docs/api: signature drift for {name}; header declares: {prototype}"
            )


def split_link_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        return target[1:target.index(">")]
    # A Markdown title may follow a path. Repository paths never contain spaces.
    return target.split(maxsplit=1)[0]


def check_links(path: Path, text: str, errors: list[str]) -> None:
    for line_number, line in enumerate(text.splitlines(), 1):
        for match in MARKDOWN_DESTINATION_RE.finditer(line):
            raw_target = split_link_target(match.group(1))
            target = unquote(raw_target.split("#", 1)[0])
            if not target or target.startswith(("http://", "https://", "mailto:", "/")):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(
                    f"{relative(path)}:{line_number}: link escapes repository: {raw_target}"
                )
                continue
            if not resolved.exists():
                errors.append(
                    f"{relative(path)}:{line_number}: broken local link: {raw_target}"
                )


def check_inline_paths(path: Path, text: str, errors: list[str]) -> None:
    """Check unambiguous repository paths shown as inline code.

    Generated `build/` products and prose placeholders are intentionally not
    treated as source paths.
    """
    doc_name = relative(path)
    if doc_name.startswith(("research/notes/", "research/archive/")):
        return

    for match in INLINE_CODE_RE.finditer(text):
        candidate = match.group(1).strip().rstrip(".,:;")
        if (
            not candidate
            or any(char.isspace() for char in candidate)
            or any(char in candidate for char in "*{}<>")
            or candidate.startswith("build/")
            or candidate.startswith("build\\")
            or candidate.startswith("emulator/web/dist/")
            or candidate in GENERATED_REPOSITORY_PATHS
        ):
            continue

        local_candidate = path.parent / candidate
        if candidate in ROOT_PATHS:
            resolved = ROOT / candidate
        elif candidate.startswith(REPOSITORY_PATH_PREFIXES):
            resolved = local_candidate if local_candidate.exists() else ROOT / candidate
        elif candidate.startswith(("./", "../")):
            resolved = path.parent / candidate
        else:
            continue

        if not resolved.resolve().exists():
            line_number = text[:match.start()].count("\n") + 1
            errors.append(
                f"{relative(path)}:{line_number}: repository path does not exist: "
                f"{candidate}"
            )


def check_text(errors: list[str]) -> None:
    for path in maintained_markdown():
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lower:
                line_number = lower[:lower.index(phrase)].count("\n") + 1
                errors.append(
                    f"{relative(path)}:{line_number}: forbidden process phrase: {phrase!r}"
                )
        for pattern, guidance in STALE_PATH_PATTERNS:
            if relative(path).startswith("research/") and "regional slot" in guidance:
                # Historical traces may record an observed pathname. They are
                # evidence, not runnable developer guidance.
                continue
            for match in pattern.finditer(text):
                line_number = text[:match.start()].count("\n") + 1
                errors.append(
                    f"{relative(path)}:{line_number}: unsafe/stale path "
                    f"{match.group(0)!r}; {guidance}"
                )
        check_links(path, text, errors)
        check_inline_paths(path, text, errors)


def mkdocs_command() -> list[str] | None:
    executable = shutil.which("mkdocs")
    if executable:
        return [executable]
    if importlib.util.find_spec("mkdocs") is not None:
        return [sys.executable, "-m", "mkdocs"]
    return None


def check_mkdocs(errors: list[str]) -> bool:
    command = mkdocs_command()
    if command is None:
        return False
    with tempfile.TemporaryDirectory(prefix="mobigo-docs-") as site_dir:
        result = subprocess.run(
            command + [
                "build",
                "--strict",
                "--config-file",
                str(CONFIG),
                "--site-dir",
                site_dir,
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode:
        errors.append("mkdocs --strict failed:\n" + result.stdout.rstrip())
    return True


def main() -> int:
    errors: list[str] = []
    check_config(errors)
    check_callable_coverage(errors)
    check_text(errors)
    mkdocs_ran = check_mkdocs(errors)

    if errors:
        print("Documentation check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    suffix = "including strict MkDocs" if mkdocs_ran else "MkDocs unavailable; strict build skipped"
    print(f"Documentation checks passed ({suffix}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
