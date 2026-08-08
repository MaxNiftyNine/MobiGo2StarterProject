#!/usr/bin/env python3
"""Enable or disable MobiGo developer mode over USB."""

from __future__ import annotations

import argparse

from device import DeviceSession, MobiGoError


DMODE_PATH = "/ETC/DMODE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--enable", action="store_true", help="enable without questions")
    action.add_argument("--disable", action="store_true", help="disable without questions")
    parser.add_argument("--device", help="device override (normally auto-detected)")
    args = parser.parse_args()

    if args.enable:
        choice = "enable"
    elif args.disable:
        choice = "disable"
    else:
        choice = input("Type enable or disable for developer mode: ").strip().lower()
        if choice not in {"enable", "disable"}:
            parser.error("answer must be enable or disable")

    try:
        with DeviceSession(args.device) as fs:
            if choice == "enable":
                fs.write_file(DMODE_PATH, b"")
                print("Developer mode enabled: created /ETC/DMODE")
            else:
                if fs.stat_size(DMODE_PATH) is None:
                    print("Developer mode is already disabled.")
                else:
                    fs.delete(DMODE_PATH)
                    print("Developer mode disabled: deleted /ETC/DMODE")
        print ("reboot your mobigo")
        return 0
    except (MobiGoError, OSError, ValueError) as exc:
        if ("closing file failed (device status -1)" in str(exc)):
            print ("Reboot your mobigo, it should be in dev mode now")
            return 0

        print(f"developer_mode: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
