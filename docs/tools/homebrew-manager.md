# Homebrew Manager

[MobiGo2HomebrewManager](https://github.com/MaxNiftyNine/MobiGo2HomebrewManager)
is the cross-platform graphical companion for Homebrew Launcher. It is linked
into this repository at `tools/homebrew-manager/` as a submodule.

The main view lists the `.MBA` applications below `/HB`. Files can be added by
dragging them into the window or selecting them with the file picker; existing
applications can be downloaded or removed. Application names retain the
`.MBA` suffix shown by the launcher.

On first use, the manager offers a guarded SY installation:

1. discover the device's actual SY entry rather than guessing a regional name;
2. download it to a verified local recovery backup;
3. create `/HB` and upload the original menu as `/HB/SystemMenu.MBA`;
4. upload and read back the launcher catalog;
5. replace SY with `HomebrewLauncher.MBA` only after every prerequisite verifies;
6. read back the installed launcher and restore SY if final verification fails.

If the firmware does not publish a newly created `/HB` directory, the manager
stops before writing SY. A plugged-in device is never a substitute for an
untouched NAND/SPI recovery dump.

Advanced mode exposes the full file tree, copy-verified rename, upload,
download, delete, and the firmware dmode setting. These operations can make the
device unbootable; keep a recovery copy and use the normal homebrew view when
possible.

Packaged Windows, macOS, and Linux builds are published on the standalone
repository's Releases page. Run the source checkout from inside the submodule:

```sh
cd tools/homebrew-manager
python3 -m mobigo_homebrew_manager
```
