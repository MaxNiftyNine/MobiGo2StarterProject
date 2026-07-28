#!/usr/bin/env python3
"""Show total, used, and free MobiGo filesystem storage."""

from __future__ import annotations

import argparse

from device import DeviceSession, MobiGoError, format_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="run immediately without the ready question"
    )
    parser.add_argument("--device", help="device override (normally auto-detected)")
    args = parser.parse_args()
    if not args.check:
        input("Connect the MobiGo in USB mode, then press Enter to check storage: ")
    try:
        with DeviceSession(args.device) as fs:
            total, free = fs.info()
        used = total - free
        print(f"Total: {format_bytes(total)} ({total} bytes)")
        print(f"Used:  {format_bytes(used)} ({used} bytes)")
        print(f"Free:  {format_bytes(free)} ({free} bytes)")
        return 0
    except (MobiGoError, OSError, ValueError) as exc:
        print(f"storage: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
