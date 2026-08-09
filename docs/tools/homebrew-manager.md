# Homebrew Manager

[MobiGo2HomebrewManager](https://github.com/MaxNiftyNine/MobiGo2HomebrewManager)
is the cross-platform graphical companion for Homebrew Launcher. It is linked
into this repository at `tools/homebrew-manager/` as a submodule.

The main view lists the `.MBA` applications below `/HB`. Files can be added by
dragging them into the window or selecting them with the file picker; existing
applications can be downloaded or removed. Application names retain the
`.MBA` suffix shown by the launcher.

When a same-stem `.HBI` file accompanies an upload, the Manager imports its
title into `/HB/INDEX.HB`. The launcher's picture comes from the palette and
menu-art bytes already embedded in the `.MBA`, not from Manager metadata.
Titles are preserved across rename, delete, refresh, and launcher updates. An
older launcher can be updated without overwriting `/HB/System.MBA`; that file
always remains the original recovery menu.

On first use, the manager offers a guarded SY installation:

1. discover the device's actual SY entry rather than guessing a regional name;
2. download it to a verified local recovery backup;
3. create and rediscover `/HB`, then upload the original menu as `/HB/System.MBA`;
4. upload and read back the launcher catalog;
5. replace SY with `HomebrewLauncher.MBA` only after every prerequisite verifies;
6. read back the installed launcher and restore SY if final verification fails.

`System.MBA` cannot be deleted on its own. **Delete all homebrew and exit**
first writes and verifies another local backup, restores `System.MBA` to the
discovered regional SY entry, and only then removes the complete `/HB` tree.
If restoration fails, the active launcher is rolled back and `/HB` is retained.

Creation, rediscovery, file transfer, rename, deletion, empty-directory removal,
launcher installation, complete uninstall, and D-mode behavior have been
verified on a physical US MobiGo 2. A plugged-in device is never a substitute
for an untouched NAND/SPI recovery dump, and other firmware regions/revisions
still require the same read-back checks.

Advanced mode exposes the full file tree, copy-verified rename, upload,
download, delete, and the firmware dmode setting. These operations can make the
device unbootable; keep a recovery copy and use the normal homebrew view when
possible.

The standalone repository publishes one portable Python-source ZIP instead of
platform-specific `.app` or `.exe` wrappers. Install its requirements, then run
the Manager from an elevated terminal so raw-device errors remain visible:

```sh
cd tools/homebrew-manager
python3 -m pip install -r requirements.txt
sudo python3 mobigo_manager.py
```

On Windows, use an Administrator PowerShell and run
`py mobigo_manager.py`. Linux graphical sessions generally need
`sudo --preserve-env=DISPLAY,XAUTHORITY python3 mobigo_manager.py`.
