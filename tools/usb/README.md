# MobiGo 2 USB tools

These scripts manage a connected MobiGo 2 without Learning Lodge. They support
macOS and Windows and provide three intentionally small workflows:

- enable or disable developer mode by creating or deleting the blank
  `/ETC/DMODE` file;
- install an MBA over USB as G1 (Hamster Highway), as the SY system menu, or at
  the filesystem root for developer-mode launching;
- delete a named remote file;
- report total, used, and free device storage.

The scripts auto-detect the VTech `USB-MSDC DISK A` device and refuse unrelated
disks. They temporarily dismount its normal volume while talking to the
filesystem mailbox. Do not unplug the console while a write is running.

## macOS setup

Install Python 3. Grant **Full Disk Access** to Terminal (or the app launching
the command) in **System Settings → Privacy & Security → Full Disk Access**.
The `.command` launchers ask for an administrator password because raw USB disk
access requires it.

Double-click a launcher and answer its question:

```text
scripts/usb/developer_mode.command
scripts/usb/install_mba.command
scripts/usb/storage.command
```

They can also be run non-interactively:

```sh
./scripts/usb/developer_mode.command --enable
./scripts/usb/developer_mode.command --disable
./scripts/usb/install_mba.command --g1 build/MobiGo2Starter.MBA
./scripts/usb/install_mba.command --system build/MobiGo2Starter.MBA
./scripts/usb/install_mba.command --root build/MobiGo2Starter.MBA
./scripts/usb/storage.command --check
```

`--sy` is an alias for `--system`. Install and developer-mode action flags skip
questions. Deletion always requires a `y` or `n` safety answer.

## Windows setup

Install Python 3, then install the one Windows USB dependency from an
Administrator PowerShell:

```powershell
py -3 -m pip install -r .\tools\mobigo_usb\requirements-windows.txt
```

Run the `.bat` launchers as Administrator:

```text
scripts\usb\developer_mode.bat
scripts\usb\install_mba.bat
scripts\usb\storage.bat
```

Non-interactive examples:

```powershell
.\scripts\usb\developer_mode.bat --disable
.\scripts\usb\install_mba.bat --g1 .\build\MobiGo2Starter.MBA
.\scripts\usb\install_mba.bat --system .\build\MobiGo2Starter.MBA
.\scripts\usb\install_mba.bat --root .\build\MobiGo2Starter.MBA
.\scripts\usb\storage.bat --check
```

Close VTech AgentMonitor, DownloadManager, and Learning Lodge before using the
Windows scripts so they do not compete for the device.

## Install targets and safety

The G1 and SY filenames differ between firmware regions. The installer lists
the applicable directory and replaces the single existing file ending in
`G1.MBA` or `SY.MBA`; it does not hard-code `135800` or `135804`.
For example, it finds `135800SY.MBA` on a US model when that is the existing
filename, while the included emulator NAND currently contains `135804SY.MBA`.

- `--g1` replaces Hamster Highway. Use it only with a G1-linked MBA.
  Learning Lodge may restore the retail game later.
- `--system` replaces the system menu. A broken MBA here can prevent normal
  startup, so use it only with recovery backups and a payload designed for the
  SY slot.
- `--root` writes the MBA at `/NAME.MBA`. Enable developer mode separately to
  make developer-mode launch paths available.

The included starter MBA is built for the SY entry at `0x0DFC1D`; install it
with `--system`. It is not interchangeable with a G1-linked MBA. Always keep
device recovery dumps, and test in the emulator first.

## Delete a MBA

To remove a MBA later, provide its absolute device path:

```sh
./scripts/usb/install_mba.command --delete /MobiGo2Starter.MBA
```

The command checks that the file exists and deletes it. Every deletion, including `--delete`, prints the warning and requires an
explicit `y` confirmation:

> **WARNING:** deleting the wrong MobiGo file can brick the console.

Delete only a file you intentionally installed. In particular, do not delete
system, boot, or recovery files to experiment.

For manual or diagnostic use, the Python entry points accept `--help`:

```sh
python3 tools/usb/developer_mode.py --help
python3 tools/usb/install_mba.py --help
python3 tools/usb/storage.py --help
```
