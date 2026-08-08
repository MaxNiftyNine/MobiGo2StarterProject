#!/usr/bin/env python3
"""Install an MBA on the MobiGo or delete a named remote file."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from device import DeviceSession, MobiGoError


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from mba_profile import require_mba_profile


def choose_install_interactively(parser: argparse.ArgumentParser) -> tuple[str, Path]:
    source = Path(input("Path to the MBA file: ").strip()).expanduser()
    target = input("Type g1, system, or root for the install location: ").strip().lower()
    aliases = {"g1": "g1", "system": "system", "sy": "system", "root": "root"}
    if target not in aliases:
        parser.error("target must be g1, system (or sy), or root")
    return aliases[target], source


def slot_path(fs, slot: str) -> str:
    directory = "/BUNDLE/G1" if slot == "g1" else "/BUNDLE/SY"
    suffix = "G1.MBA" if slot == "g1" else "SY.MBA"
    matches = [
        entry.name
        for entry in fs.listdir(directory)
        if entry.kind == 1 and entry.name.upper().endswith(suffix)
    ]
    if len(matches) != 1:
        raise MobiGoError(
            f"expected one {suffix} file in {directory}, found {len(matches)}"
        )
    return f"{directory}/{matches[0]}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--g1", metavar="MBA", type=Path, help="overwrite G1")
    target.add_argument(
        "--system", "--sy", dest="system", metavar="MBA", type=Path,
        help="overwrite the system menu",
    )
    target.add_argument(
        "--root", metavar="MBA", type=Path, help="put the MBA at filesystem root"
    )
    target.add_argument(
        "--delete",
        metavar="REMOTE_PATH",
        help="delete one remote file after a y/n safety confirmation",
    )
    parser.add_argument("--device", help="device override (normally auto-detected)")
    parser.add_argument(
        "--allow-unverified-profile",
        action="store_true",
        help=(
            "allow unknown launch metadata for an SY/G1 install after manual "
            "verification; a known cross-slot profile is still rejected"
        ),
    )
    args = parser.parse_args()

    delete_path: str | None = None
    if args.delete is not None:
        delete_path = args.delete
        selected, source = "", Path()
    elif args.g1 is not None:
        selected, source = "g1", args.g1
    elif args.system is not None:
        selected, source = "system", args.system
    elif args.root is not None:
        selected, source = "root", args.root
    else:
        operation = input("Type install or delete: ").strip().lower()
        if operation == "delete":
            delete_path = input(
                "Remote file to delete (for example /MobiGo2Starter.MBA): "
            ).strip()
            selected, source = "", Path()
        elif operation == "install":
            selected, source = choose_install_interactively(parser)
        else:
            parser.error("answer must be install or delete")

    if delete_path is not None:
        if not delete_path.startswith("/") or delete_path == "/":
            parser.error("remote delete path must be an absolute file path")
        print("WARNING: deleting the wrong MobiGo file can brick the console.")
        confirmation = input(f"Delete {delete_path}? [y/N] ").strip().lower()
        if confirmation not in {"y", "yes"}:
            print("Delete cancelled; nothing was changed.")
            return 0
        try:
            with DeviceSession(args.device) as fs:
                size = fs.stat_size(delete_path)
                if size is None:
                    raise MobiGoError(f"remote file does not exist: {delete_path}")
                fs.delete(delete_path)

                print(f"deleted {delete_path} ({size} bytes)")
            return 0
        except (MobiGoError, OSError, UnicodeError, ValueError) as exc:
            print(f"install_mba: {exc}")
            return 1

    source = source.expanduser().resolve()
    if not source.is_file():
        parser.error(f"MBA file does not exist: {source}")
    if source.suffix.lower() != ".mba":
        parser.error("input file must have an .MBA extension")
    data = source.read_bytes()
    if not data.startswith(b"bM_gbMQa"):
        parser.error("input does not have a recognized MBA header")
    if selected in {"g1", "system"}:
        try:
            require_mba_profile(
                data,
                "G1" if selected == "g1" else "SY",
                allow_unverified=args.allow_unverified_profile,
            )
        except ValueError as exc:
            parser.error(str(exc))

    try:
        with DeviceSession(args.device) as fs:
            if selected == "root":
                filename = source.name
                remote = "/" + filename
                if len(("A:" + remote).encode("ascii")) > 42:
                    raise MobiGoError("MBA filename is too long for the device")
            else:
                remote = slot_path(fs, selected)
            print(f"Writing {len(data)} bytes to {remote}. Do not disconnect USB.")
            fs.write_file(remote, data)
            written = fs.stat_size(remote)
            if written != len(data):
                raise MobiGoError(
                    f"write verification failed: device reports {written} bytes"
                )
            print(f"PASS installed {source.name} as {remote}")
        return 0
    except (MobiGoError, OSError, UnicodeError, ValueError) as exc:
        print(f"install_mba: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
