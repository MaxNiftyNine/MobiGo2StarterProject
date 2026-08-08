#!/usr/bin/env python3
"""Run the three complete SDK examples through a real firmware boot.

The verifier intentionally launches generated MBA files through the retail
menus.  It does not direct-jump to application code, and the emulator's MBA
overlay remains transient.  Relevant stdout and framebuffer captures are
kept under build/sample-emulator-check for failure diagnosis.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from emulator_support import ensure_nand, find_emulator, mba_overlay_arguments


PROGRESS_RE = re.compile(
    r"^EMU STATE insns=(\d+) cycles=(\d+) pc=0x([0-9a-fA-F]+)\b",
    re.MULTILINE,
)
STOP_RE = re.compile(
    r"^Stopped after (\d+) instructions at PC=0x([0-9a-fA-F]+)\b",
    re.MULTILINE,
)
REPLACEMENT_RE = re.compile(
    r"^Replaced (.+) in (\d+)(?: of (\d+))? filesystem snapshots\.$",
    re.MULTILINE,
)
FRAME_RE = re.compile(r"_insn_(\d+)\.bmp$")

HAMSTER_HIGHWAY = "350000000,10000000,165,82"
EASY = "680000000,10000000,100,205"


class VerificationError(RuntimeError):
    """An actionable sample-runtime verification failure."""

    def __init__(
        self,
        sample: str,
        message: str,
        *,
        output_path: Path | None = None,
        frame_dir: Path | None = None,
        output: str = "",
    ) -> None:
        super().__init__(message)
        self.sample = sample
        self.output_path = output_path
        self.frame_dir = frame_dir
        self.output = output


@dataclass(frozen=True)
class ProgressState:
    instructions: int
    cycles: int
    pc: int


@dataclass(frozen=True)
class FrameStats:
    path: Path
    instructions: int
    digest: str
    colors: frozenset[tuple[int, int, int]]
    nonblack_pixels: int
    nonwhite_pixels: int

    @property
    def nonuniform(self) -> bool:
        return len(self.colors) > 1


@dataclass(frozen=True)
class SampleSpec:
    name: str
    build_directory: str
    mba_name: str
    target: str
    role: str
    steps: int
    frame_interval: int
    touch_events: tuple[str, ...] = ()
    key_events: tuple[str, ...] = ()
    expect_poweroff: bool = False


@dataclass(frozen=True)
class SampleResult:
    name: str
    seconds: float
    stopped_instructions: int
    entry: int
    payload_end: int
    first_payload_instructions: int
    payload_progress_samples: int
    post_launch_frames: int
    distinct_post_launch_frames: int
    detail: str


SAMPLES = (
    SampleSpec(
        name="color-cycle",
        build_directory="color-cycle",
        mba_name="ColorCycle.MBA",
        target="system",
        role="MGB_SYS",
        steps=285_000_000,
        frame_interval=5_000_000,
        key_events=("250000000,30000000,off",),
        expect_poweroff=True,
    ),
    SampleSpec(
        name="bad-apple",
        build_directory="movie-player",
        mba_name="MonochromeMoviePlayer.MBA",
        target="g1",
        role="MGB_G1",
        steps=930_000_000,
        frame_interval=20_000_000,
        touch_events=(HAMSTER_HIGHWAY, EASY),
    ),
    SampleSpec(
        name="celeste",
        build_directory="celeste",
        mba_name="MobiGoCeleste.MBA",
        target="g1",
        role="MGB_G1",
        steps=950_000_000,
        frame_interval=20_000_000,
        touch_events=(HAMSTER_HIGHWAY, EASY),
        # E is the documented keyboard dash alternative; D is move right.
        key_events=(
            "900000000,8000000,e",
            "920000000,10000000,d",
        ),
    ),
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def payload_interval(build: Path, sample: str) -> tuple[int, int]:
    entry_path = build / "entry.txt"
    payload_path = build / "app.bin"
    missing = [str(path) for path in (entry_path, payload_path) if not path.is_file()]
    if missing:
        raise VerificationError(
            sample,
            "missing built payload files: " + ", ".join(missing) +
            "; run `make samples`",
        )
    try:
        entry = int(entry_path.read_text(encoding="ascii").strip(), 0)
    except (OSError, UnicodeError, ValueError) as error:
        raise VerificationError(
            sample,
            f"invalid entry.txt at {entry_path}: {error}",
        ) from error
    payload_words = (payload_path.stat().st_size + 1) // 2
    if entry <= 0 or payload_words <= 0:
        raise VerificationError(
            sample,
            f"invalid payload interval entry={entry:#x}, words={payload_words}",
        )
    return entry, entry + payload_words


def parse_progress(output: str, sample: str) -> list[ProgressState]:
    states = [
        ProgressState(int(insns), int(cycles), int(pc, 16))
        for insns, cycles, pc in PROGRESS_RE.findall(output)
    ]
    if not states:
        raise VerificationError(sample, "emulator emitted no progress states")
    for previous, current in zip(states, states[1:]):
        if current.instructions <= previous.instructions:
            raise VerificationError(
                sample,
                "progress instruction count did not increase: "
                f"{previous.instructions} -> {current.instructions}",
            )
        if current.cycles <= previous.cycles:
            raise VerificationError(
                sample,
                "guest-visible cycle count did not increase: "
                f"{previous.cycles} -> {current.cycles}",
            )
    return states


def read_frame(path: Path) -> FrameStats:
    match = FRAME_RE.search(path.name)
    if match is None:
        raise ValueError(f"frame filename has no instruction count: {path.name}")
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError("not a complete BMP file")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    signed_height = struct.unpack_from("<i", data, 22)[0]
    bits_per_pixel = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    if (width, abs(signed_height)) != (320, 240):
        raise ValueError(
            f"unexpected dimensions {(width, abs(signed_height))}, expected (320, 240)"
        )
    if signed_height == 0 or bits_per_pixel != 32 or compression != 0:
        raise ValueError(
            "unexpected BMP encoding: "
            f"height={signed_height}, bpp={bits_per_pixel}, compression={compression}"
        )
    pixel_bytes = width * abs(signed_height) * 4
    end = pixel_offset + pixel_bytes
    if end > len(data):
        raise ValueError(
            f"truncated BMP pixel data: need {end} bytes, found {len(data)}"
        )
    raw = data[pixel_offset:end]
    colors: set[tuple[int, int, int]] = set()
    nonblack = 0
    nonwhite = 0
    for offset in range(0, len(raw), 4):
        blue, green, red = raw[offset : offset + 3]
        color = (red, green, blue)
        colors.add(color)
        if color != (0, 0, 0):
            nonblack += 1
        if color != (255, 255, 255):
            nonwhite += 1
    return FrameStats(
        path=path,
        instructions=int(match.group(1)),
        digest=hashlib.sha256(raw).hexdigest(),
        colors=frozenset(colors),
        nonblack_pixels=nonblack,
        nonwhite_pixels=nonwhite,
    )


def read_frames(frame_dir: Path, sample: str) -> list[FrameStats]:
    paths = sorted(frame_dir.glob("*.bmp"))
    if not paths:
        raise VerificationError(sample, f"no framebuffer captures in {frame_dir}")
    frames: list[FrameStats] = []
    for path in paths:
        try:
            frames.append(read_frame(path))
        except (OSError, struct.error, ValueError) as error:
            raise VerificationError(
                sample,
                f"invalid framebuffer capture {path}: {error}",
            ) from error
    return frames


def validate_overlay(
    spec: SampleSpec,
    output: str,
    entry: int,
) -> None:
    expected_metadata = (
        f"target={spec.target}, role={spec.role}, entry={entry:#x}"
    ).lower()
    if "Applied transient MBA overlay:" not in output:
        raise VerificationError(spec.name, "transient MBA overlay was not reported")
    if expected_metadata not in output.lower():
        raise VerificationError(
            spec.name,
            "overlay metadata mismatch; expected " + expected_metadata,
        )
    if "The NAND file on disk will not be modified." not in output:
        raise VerificationError(spec.name, "overlay did not report transient NAND behavior")
    replacements = REPLACEMENT_RE.findall(output)
    slot = "SY" if spec.target == "system" else "G1"
    matching = [
        (path, int(replaced), int(total) if total else int(replaced))
        for path, replaced, total in replacements
        if f"/BUNDLE/{slot}/" in path.upper()
    ]
    if not matching:
        raise VerificationError(
            spec.name,
            f"overlay did not report a suffix-discovered /BUNDLE/{slot}/ path",
        )
    if any(replaced <= 0 or replaced > total for _, replaced, total in matching):
        raise VerificationError(
            spec.name,
            f"invalid filesystem-snapshot replacement counts: {matching}",
        )


def validate_color_cycle(frames: list[FrameStats], sample: str) -> str:
    solid_nonwhite = {
        next(iter(frame.colors))
        for frame in frames
        if len(frame.colors) == 1
        and next(iter(frame.colors)) not in {(0, 0, 0), (255, 255, 255)}
    }
    if len(solid_nonwhite) < 2:
        raise VerificationError(
            sample,
            "color cycle did not produce at least two distinct solid, nonwhite "
            f"post-entry colors (found {sorted(solid_nonwhite)})",
        )
    return f"colors={len(solid_nonwhite)} power=off"


def validate_bad_apple(frames: list[FrameStats], sample: str) -> str:
    black_and_white = frozenset({(0, 0, 0), (255, 255, 255)})
    monochrome = [frame for frame in frames if frame.colors == black_and_white]
    distinct = {frame.digest for frame in monochrome}
    if len(monochrome) < 3:
        raise VerificationError(
            sample,
            "Bad Apple produced fewer than three nonuniform monochrome "
            f"post-entry frames (found {len(monochrome)})",
        )
    if len(distinct) < 3:
        raise VerificationError(
            sample,
            "Bad Apple post-entry framebuffer did not change several times "
            f"(distinct monochrome frames={len(distinct)})",
        )
    return f"monochrome_frames={len(monochrome)} distinct={len(distinct)}"


def validate_celeste(frames: list[FrameStats], sample: str) -> str:
    nonuniform = [frame for frame in frames if frame.nonuniform]
    distinct = {frame.digest for frame in nonuniform}
    if len(nonuniform) < 3 or len(distinct) < 2:
        raise VerificationError(
            sample,
            "Celeste did not produce distinct, nonuniform post-entry frames "
            f"(nonuniform={len(nonuniform)}, distinct={len(distinct)})",
        )
    # The final injected key releases at 930M instructions.  Requiring a
    # nonuniform capture after that point proves the game continued to render
    # while processing the representative dash/right input sequence.
    post_input = [frame for frame in nonuniform if frame.instructions > 930_000_000]
    if not post_input:
        raise VerificationError(
            sample,
            "Celeste produced no nonuniform frame after the injected dash/right input",
        )
    return (
        f"nonuniform_frames={len(nonuniform)} distinct={len(distinct)} "
        "input=E+D"
    )


def run_sample(
    root: Path,
    emulator: Path,
    nand: Path,
    artifact_root: Path,
    spec: SampleSpec,
) -> SampleResult:
    build = root / "build" / spec.build_directory
    mba = build / spec.mba_name
    if not mba.is_file():
        raise VerificationError(
            spec.name,
            f"missing {mba}; run `make samples`",
        )
    entry, payload_end = payload_interval(build, spec.name)

    sample_artifacts = artifact_root / spec.name
    frame_dir = sample_artifacts / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    output_path = sample_artifacts / "emulator.stdout.txt"
    command_path = sample_artifacts / "command.json"

    command = [
        str(emulator),
        "--rom", str(root / "vendor" / "firmware" / "internalrom.bin"),
        "--spi", str(root / "vendor" / "firmware" / "spi.bin"),
        *mba_overlay_arguments(root, mba),
        "--mode", "fast",
        "--no-window",
        "--steps", str(spec.steps),
        "--dump-frame-dir", str(frame_dir),
        "--dump-frame-interval", str(spec.frame_interval),
    ]
    for event in spec.touch_events:
        command.extend(("--touch-event", event))
    for event in spec.key_events:
        command.extend(("--key-event", event))
    command_path.write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")

    nand_before = file_sha256(nand)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=300,
        )
        output = completed.stdout
    except subprocess.TimeoutExpired as error:
        output = error.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        output_path.write_text(output, encoding="utf-8")
        raise VerificationError(
            spec.name,
            "emulator exceeded the 300-second timeout",
            output_path=output_path,
            frame_dir=frame_dir,
            output=output,
        ) from error
    seconds = time.monotonic() - started
    output_path.write_text(output, encoding="utf-8")

    def fail(message: str) -> None:
        raise VerificationError(
            spec.name,
            message,
            output_path=output_path,
            frame_dir=frame_dir,
            output=output,
        )

    nand_after = file_sha256(nand)
    if nand_after != nand_before:
        fail(
            "base NAND changed during a supposedly transient overlay "
            f"({nand_before[:12]} -> {nand_after[:12]})"
        )
    if completed.returncode != 0:
        fail(f"emulator exited with status {completed.returncode}")
    try:
        validate_overlay(spec, output, entry)
        states = parse_progress(output, spec.name)
    except VerificationError as error:
        fail(str(error))
        raise AssertionError("unreachable") from error

    payload_states = [state for state in states if entry <= state.pc < payload_end]
    if not payload_states:
        fail(
            "no sampled PC entered the built payload interval "
            f"[{entry:#x}, {payload_end:#x})"
        )
    first_payload = payload_states[0].instructions
    final_progress = states[-1]
    if not entry <= final_progress.pc < payload_end:
        fail(
            "last sampled PC left the payload interval after launch: "
            f"pc={final_progress.pc:#x}, interval=[{entry:#x}, {payload_end:#x})"
        )

    stop = STOP_RE.search(output)
    if stop is None:
        fail("emulator emitted no final stop state")
    stopped_instructions = int(stop.group(1))
    if spec.expect_poweroff:
        if "Power state: off" not in output:
            fail("Off input did not reach the powered-off terminal state")
        if not 250_000_000 < stopped_instructions <= spec.steps:
            fail(
                "powered off outside the expected post-input interval: "
                f"stopped={stopped_instructions}, limit={spec.steps}"
            )
    else:
        if "Power state: off" in output:
            fail("sample unexpectedly entered the powered-off terminal state")
        if stopped_instructions != spec.steps:
            fail(
                f"emulator stopped at {stopped_instructions}, expected {spec.steps}"
            )

    try:
        all_frames = read_frames(frame_dir, spec.name)
    except VerificationError as error:
        fail(str(error))
        raise AssertionError("unreachable") from error
    post_launch = [
        frame for frame in all_frames
        if frame.instructions >= first_payload
    ]
    if len(post_launch) < 2:
        fail(
            "fewer than two framebuffer captures followed sampled payload entry "
            f"at {first_payload} instructions"
        )
    distinct_post_launch = len({frame.digest for frame in post_launch})

    try:
        if spec.name == "color-cycle":
            detail = validate_color_cycle(post_launch, spec.name)
        elif spec.name == "bad-apple":
            detail = validate_bad_apple(post_launch, spec.name)
        elif spec.name == "celeste":
            detail = validate_celeste(post_launch, spec.name)
        else:
            raise VerificationError(spec.name, "no sample-specific validator")
    except VerificationError as error:
        fail(str(error))
        raise AssertionError("unreachable") from error

    return SampleResult(
        name=spec.name,
        seconds=seconds,
        stopped_instructions=stopped_instructions,
        entry=entry,
        payload_end=payload_end,
        first_payload_instructions=first_payload,
        payload_progress_samples=len(payload_states),
        post_launch_frames=len(post_launch),
        distinct_post_launch_frames=distinct_post_launch,
        detail=detail,
    )


def failure_tail(output: str, limit: int = 14) -> str:
    lines = [line for line in output.splitlines() if line.strip()]
    return "\n".join(lines[-limit:])


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    artifact_root = root / "build" / "sample-emulator-check"
    if artifact_root.exists():
        shutil.rmtree(artifact_root)
    artifact_root.mkdir(parents=True)

    started = time.monotonic()
    results: list[SampleResult] = []
    try:
        emulator = find_emulator(root)
        nand = ensure_nand(root)
        for spec in SAMPLES:
            result = run_sample(root, emulator, nand, artifact_root, spec)
            results.append(result)
            print(
                f"PASS {result.name} {result.seconds:.1f}s "
                f"entry={result.entry:#x}@{result.first_payload_instructions} "
                f"frames={result.post_launch_frames}/"
                f"{result.distinct_post_launch_frames} {result.detail}",
                flush=True,
            )
    except VerificationError as error:
        print(f"FAIL {error.sample}: {error}", file=sys.stderr)
        if error.output_path is not None:
            print(f"  stdout: {error.output_path}", file=sys.stderr)
        if error.frame_dir is not None:
            print(f"  frames: {error.frame_dir}", file=sys.stderr)
        tail = failure_tail(error.output)
        if tail:
            print("  emulator output tail:", file=sys.stderr)
            for line in tail.splitlines():
                print(f"    {line}", file=sys.stderr)
        print(f"  artifacts: {artifact_root}", file=sys.stderr)
        return 1
    except (FileNotFoundError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL setup: {error}", file=sys.stderr)
        print(f"  artifacts: {artifact_root}", file=sys.stderr)
        return 1

    total_seconds = time.monotonic() - started
    summary = {
        "total_seconds": total_seconds,
        "results": [
            {
                "name": result.name,
                "seconds": result.seconds,
                "stopped_instructions": result.stopped_instructions,
                "entry": result.entry,
                "payload_end": result.payload_end,
                "first_payload_instructions": result.first_payload_instructions,
                "payload_progress_samples": result.payload_progress_samples,
                "post_launch_frames": result.post_launch_frames,
                "distinct_post_launch_frames": result.distinct_post_launch_frames,
                "detail": result.detail,
            }
            for result in results
        ],
    }
    (artifact_root / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"PASS complete-samples total={total_seconds:.1f}s "
        f"artifacts={artifact_root}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
