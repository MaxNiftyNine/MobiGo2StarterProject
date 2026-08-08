# MobiGo 2 physical USB tools

These guarded tools use the console's filesystem mailbox without Learning
Lodge. They can toggle developer mode, inspect storage, install an MBA at the
discovered SY/G1/root destination, and delete an explicitly named file.

They support **macOS and Windows**. Linux supports the SDK build, emulator,
tests, and copied-NAND tools, but the physical raw-device discovery/dismount
backend is not implemented there.

## Safety contract

- The transport accepts only the expected `USB-MSDC DISK A` layout.
- Keep a verified recovery backup before writing the system slot.
- Do not unplug or power off during a write/read-back operation.
- Let the installer discover the existing regional slot pathname.
- Match the linked MBA role to the selected install role.
- Close Learning Lodge, AgentMonitor, and other software that may own the
  device.

The default project is SY. Replacing physical SY is high risk even though SY is
the canonical development target. G1 installation is only for a G1-linked
legacy project.

Before an SY/G1 write, the installer validates the MBA's complete launch
metadata. It always rejects a known cross-slot profile. An unknown profile also
fails closed unless a developer who has independently reviewed it supplies
`--allow-unverified-profile`; that flag never permits a known SY↔G1 mismatch.

## macOS

Install Python 3 and grant the launching terminal **Full Disk Access**. The
`.command` launchers request administrator access for the raw disk:

```sh
./scripts/usb/developer_mode.command --enable
./scripts/usb/install_mba.command --system build/MobiGo2Starter.MBA
./scripts/usb/storage.command --check
```

Interactive use is available by double-clicking the same launchers. `--sy` is
an alias for `--system`.

## Windows

Install Python 3, then install the raw-volume dependency from an Administrator
PowerShell:

```powershell
py -3 -m pip install -r .\tools\usb\requirements-windows.txt
```

Run the launchers as Administrator:

```powershell
.\scripts\usb\developer_mode.bat --enable
.\scripts\usb\install_mba.bat --system .\build\MobiGo2Starter.MBA
.\scripts\usb\storage.bat --check
```

## Legacy G1 and root installs

Use `--g1` only with an artifact built for `target: "game1"`. Use `--root` for
a deliberately configured developer-mode workflow. Neither option converts an
SY-linked MBA into another role.

## Deletion

Deletion is destructive and always asks for confirmation. Supply only an
absolute device path that you intentionally installed:

```sh
./scripts/usb/install_mba.command --delete /MyHomebrew.MBA
```

Never delete a boot, system, recovery, or unknown file. For complete Python
options, run `python3 tools/usb/install_mba.py --help`.
