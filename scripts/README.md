# Desktop launchers

The canonical cross-platform interface is:

```sh
python3 tools/mobigo.py doctor
python3 tools/mobigo.py run
```

The `scripts/build_and_run.*` files are thin compatibility launchers for macOS,
Windows, and Linux. They delegate to maintained implementations under `tools/`
and must not grow a second build policy.

`scripts/usb/` contains physical-device launchers for macOS and Windows.
Physical USB transport is not currently implemented for Linux; Linux supports
the normal build, test, emulator, and copied-NAND workflows.
