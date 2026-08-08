# NAND and USB tools

NAND tools edit copies directly on the host. USB tools communicate with a
physical MobiGo 2 through its firmware-visible storage mailbox.

## Assemble the development NAND

```sh
python3 tools/nand/assemble_nand.py
```

This reconstructs `vendor/firmware/nand.us-stitched.bin` from tracked parts and
verifies size and SHA-256.

## Create a copied NAND

```sh
python3 tools/mobigo.py build --nand
```

The output is `build/nand.edited.bin`. The installer discovers the selected slot
file and reads the finished MBA back for exact comparison.

## Physical USB prerequisites

Close Learning Lodge and related VTech background applications before taking
exclusive access to the device. Windows additionally needs:

```powershell
py -3 -m pip install -r .\tools\usb\requirements-windows.txt
```

On macOS, raw disk access requires Full Disk Access for the terminal/application
and administrator privileges. Physical USB transport is not implemented on
Linux; Linux supports build, test, emulator, and copied-NAND workflows.

## Install targets

Compatibility launchers remain under `scripts/usb/`:

```sh
./scripts/usb/install_mba.command --system build/MobiGo2Starter.MBA
```

The default starter is SY and must use `--system`. For a deliberately G1-linked
project, pass that project's output to `--g1`. Never use the default starter as
a G1 example.

`--root` supports a developer-mode root file but does not convert its profile.
The installer discovers regional filenames for system and G1 targets.

Persistent SY/G1 installs parse the MBA's complete launch metadata. A known
cross-slot file is rejected even if `--allow-unverified-profile` is supplied.
The override exists only for manually reviewed metadata that matches neither
known profile; omit it in normal builds so unknown files fail closed.

## Developer mode and storage

```sh
./scripts/usb/developer_mode.command --enable
./scripts/usb/developer_mode.command --disable
./scripts/usb/storage.command --check
```

Windows uses the corresponding `.bat` launchers. Low-level Python entry points
under `tools/usb/` provide `--help` for diagnostic use.

## Safety

Every physical write requires stable power, verified recovery dumps, and the
correct linked target. Deletion should remain interactive and must never be
used to experiment on boot/system files.
