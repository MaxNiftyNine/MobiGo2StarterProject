#!/usr/bin/env python3
"""Minimal cross-platform client for the MobiGo 2 USB filesystem mailbox.

The macOS transport is based on the validated implementation in
/Volumes/Untitled/MobiGoRE. The Windows transport follows the raw-volume
approach in MaxNiftyNine/VTech-MobiGo2-Reverse-Engineering-Dump.
"""

from __future__ import annotations

import glob
import json
import os
import plistlib
import re
import struct
import subprocess
import sys
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


BLOCK_SIZE = 512
MAX_TRANSFER = 0x10000
MAILBOX_ADDRESS = 0x00280000
READ_DATA_LBA = 0x3B00
WRITE_DATA_LBA = 0x3C00
READ_SETUP_LBA = 0x3D28
WRITE_SETUP_LBA = 0x3D2A
DEVICE_MODEL = "USB-MSDC DISK A"
MODE_READ = 1
MODE_WRITE = 2


class MobiGoError(RuntimeError):
    pass


class _PosixBackend:
    def __init__(self, path: str):
        self.path = path
        try:
            self.fd = os.open(path, os.O_RDWR)
        except PermissionError as exc:
            advice = "rerun with sudo"
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                advice = "grant Full Disk Access to Terminal, then retry"
            raise MobiGoError(f"permission denied opening {path}; {advice}") from exc
        except OSError as exc:
            raise MobiGoError(f"cannot open {path}: {exc}") from exc

    def read_at(self, offset: int, size: int) -> bytes:
        os.lseek(self.fd, offset, os.SEEK_SET)
        output = bytearray()
        while len(output) < size:
            part = os.read(self.fd, size - len(output))
            if not part:
                raise MobiGoError(f"short raw read at byte offset 0x{offset:x}")
            output.extend(part)
        return bytes(output)

    def write_at(self, offset: int, data: bytes) -> None:
        os.lseek(self.fd, offset, os.SEEK_SET)
        written = 0
        while written < len(data):
            count = os.write(self.fd, data[written:])
            if count <= 0:
                raise MobiGoError(f"short raw write at byte offset 0x{offset:x}")
            written += count

    def close(self) -> None:
        os.close(self.fd)


class _WindowsBackend:
    def __init__(self, path: str):
        try:
            import win32con
            import win32file
            import winioctlcon
        except ImportError as exc:
            raise MobiGoError(
                "Windows USB access requires pywin32; run `py -m pip install pywin32`"
            ) from exc
        self.win32con = win32con
        self.win32file = win32file
        self.handle = win32file.CreateFile(
            path,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            None,
            win32con.OPEN_EXISTING,
            0,
            None,
        )
        for code in (
            winioctlcon.FSCTL_LOCK_VOLUME,
            winioctlcon.FSCTL_DISMOUNT_VOLUME,
            winioctlcon.FSCTL_ALLOW_EXTENDED_DASD_IO,
        ):
            try:
                win32file.DeviceIoControl(self.handle, code, None, 0)
            except Exception:
                pass

    def read_at(self, offset: int, size: int) -> bytes:
        self.win32file.SetFilePointer(
            self.handle, offset, self.win32con.FILE_BEGIN
        )
        _, data = self.win32file.ReadFile(self.handle, size)
        if len(data) != size:
            raise MobiGoError(f"short raw read at byte offset 0x{offset:x}")
        return data

    def write_at(self, offset: int, data: bytes) -> None:
        self.win32file.SetFilePointer(
            self.handle, offset, self.win32con.FILE_BEGIN
        )
        _, written = self.win32file.WriteFile(self.handle, data)
        if written not in (None, len(data)):
            raise MobiGoError(f"short raw write at byte offset 0x{offset:x}")

    def close(self) -> None:
        self.handle.Close()


class MailboxTransport:
    def __init__(self, backend: _PosixBackend | _WindowsBackend):
        self.backend = backend
        self.reference_lba = self._fat_data_start()

    def _fat_data_start(self) -> int:
        boot = self.backend.read_at(0, BLOCK_SIZE)
        bytes_per_sector = struct.unpack_from("<H", boot, 11)[0]
        reserved = struct.unpack_from("<H", boot, 14)[0]
        fat_count = boot[16]
        root_entries = struct.unpack_from("<H", boot, 17)[0]
        sectors_per_fat = struct.unpack_from("<H", boot, 22)[0]
        if (
            bytes_per_sector != BLOCK_SIZE
            or reserved == 0
            or fat_count == 0
            or sectors_per_fat == 0
            or boot[54:62] != b"FAT16   "
            or boot[510:512] != b"\x55\xaa"
        ):
            raise MobiGoError("refusing unexpected transport-partition layout")
        root_sectors = (root_entries * 32 + BLOCK_SIZE - 1) // BLOCK_SIZE
        return reserved + fat_count * sectors_per_fat + root_sectors

    @staticmethod
    def _setup(size: int) -> bytes:
        blocks = (size + BLOCK_SIZE - 1) // BLOCK_SIZE
        return struct.pack(">I2sH", MAILBOX_ADDRESS, b"\x06\x00", blocks).ljust(
            BLOCK_SIZE, b"\0"
        )

    def _offset(self, lba: int) -> int:
        return (self.reference_lba + lba) * BLOCK_SIZE

    def read(self, size: int) -> bytes:
        if size <= 0 or size % BLOCK_SIZE:
            raise ValueError("mailbox reads must be positive multiples of 512")
        self.backend.write_at(self._offset(READ_SETUP_LBA), self._setup(size))
        return self.backend.read_at(self._offset(READ_DATA_LBA), size)

    def write(self, data: bytes) -> None:
        if not data or len(data) % BLOCK_SIZE:
            raise ValueError("mailbox writes must be positive multiples of 512")
        self.backend.write_at(self._offset(WRITE_SETUP_LBA), self._setup(len(data)))
        self.backend.write_at(self._offset(WRITE_DATA_LBA), data)


@dataclass(frozen=True)
class DirEntry:
    name: str
    size: int
    kind: int
    token: int


class MobiGoFS:
    def __init__(self, transport: MailboxTransport):
        self.transport = transport
        self._drive: str | None = None

    @staticmethod
    def _request(command: int) -> bytearray:
        request = bytearray(BLOCK_SIZE)
        struct.pack_into("<I", request, 0, command)
        return request

    def _path(self, request: bytearray, path: str, limit: int) -> None:
        wire = path.replace("/", "\\")
        if wire.startswith("\\"):
            if self._drive is None:
                drive = self._simple(self._request(0x16), "get current drive")
                if not ord("A") <= drive <= ord("Z"):
                    raise MobiGoError(f"device returned invalid drive {drive}")
                self._drive = chr(drive)
            wire = self._drive + ":" + wire
        encoded = wire.encode("ascii")
        if len(encoded) > limit:
            raise MobiGoError(f"device path is too long: {path}")
        request[4 : 4 + len(encoded)] = encoded

    def _exchange(self, request: bytes) -> bytes:
        self.transport.write(request)
        time.sleep(0.05)
        return self.transport.read(BLOCK_SIZE)

    @staticmethod
    def _status(response: bytes) -> int:
        return struct.unpack_from("<h", response, 0)[0]

    def _simple(self, request: bytes, operation: str) -> int:
        status = self._status(self._exchange(request))
        if status < 0:
            raise MobiGoError(f"{operation} failed (device status {status})")
        return status

    def info(self) -> tuple[int, int]:
        response = self._exchange(self._request(0x11))
        if self._status(response) < 0:
            raise MobiGoError("getting filesystem storage information failed")
        return struct.unpack_from("<II", response, 4)

    def stat_size(self, path: str) -> int | None:
        request = self._request(9)
        self._path(request, path, 42)
        response = self._exchange(request)
        if self._status(response) < 0:
            return None
        size = struct.unpack_from("<I", response, 4)[0]
        return None if size == 0xFFFFFFFF else size

    def open(self, path: str, mode: int) -> int:
        request = self._request(2)
        self._path(request, path, 42)
        struct.pack_into("<H", request, 46, mode)
        return self._simple(request, f"opening {path}")

    def close(self, handle: int) -> None:
        request = self._request(5)
        struct.pack_into("<H", request, 4, handle)
        self._simple(request, "closing file")

    def seek(self, handle: int, offset: int) -> None:
        request = self._request(0x0C)
        struct.pack_into("<IH", request, 4, offset, handle)
        self._simple(request, "seeking file")

    def truncate(self, handle: int) -> None:
        request = self._request(0x0D)
        struct.pack_into("<H", request, 4, handle)
        self._simple(request, "truncating file")

    def write_handle(self, handle: int, data: bytes) -> None:
        rounded = (len(data) + BLOCK_SIZE - 1) & ~(BLOCK_SIZE - 1)
        request = self._request(4)
        struct.pack_into("<H", request, 4, handle)
        struct.pack_into("<I", request, 8, rounded)
        self.transport.write(request)
        padded = data + bytes(rounded - len(data))
        for offset in range(0, rounded, MAX_TRANSFER):
            self.transport.write(padded[offset : offset + MAX_TRANSFER])
        time.sleep(0.05)
        if self._status(self.transport.read(BLOCK_SIZE)) < 0:
            raise MobiGoError("writing file data failed")

    def write_file(self, path: str, data: bytes) -> None:
        handle = self.open(path, MODE_WRITE)
        try:
            self.seek(handle, 0)
            self.truncate(handle)
            self.write_handle(handle, data)
            self.seek(handle, len(data))
            self.truncate(handle)
        finally:
            self.close(handle)

    def delete(self, path: str) -> None:
        request = self._request(8)
        self._path(request, path, 42)
        self._simple(request, f"deleting {path}")

    @staticmethod
    def _entries(page: bytes) -> Iterator[DirEntry]:
        for offset in range(0, BLOCK_SIZE - 27, 28):
            token = struct.unpack_from("<h", page, offset)[0]
            if token < 0:
                return
            name = page[offset + 4 : offset + 18].split(b"\0", 1)[0]
            yield DirEntry(
                name.decode("ascii", "replace"),
                struct.unpack_from("<I", page, offset + 24)[0],
                struct.unpack_from("<H", page, offset + 18)[0],
                token,
            )

    def listdir(self, path: str) -> Iterator[DirEntry]:
        request = self._request(6)
        self._path(request, path, 30)
        page = self._exchange(request)
        while True:
            entries = list(self._entries(page))
            if not entries:
                return
            yield from entries
            if len(entries) < 18:
                return
            request = self._request(7)
            struct.pack_into("<i", request, 4, entries[-1].token)
            page = self._exchange(request)


def _disk_info(device: str) -> dict:
    result = subprocess.run(
        ["diskutil", "info", "-plist", device],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        return {}
    try:
        return plistlib.loads(result.stdout)
    except Exception:
        return {}


def _mac_transport_partition(block: str) -> str:
    result = subprocess.run(
        ["diskutil", "list", "-plist", block], capture_output=True, check=False
    )
    try:
        tree = plistlib.loads(result.stdout)
        partitions = tree["AllDisksAndPartitions"][0]["Partitions"]
        identifier = next(
            p["DeviceIdentifier"]
            for p in partitions
            if p.get("Content") == "DOS_FAT_16_S"
        )
    except (Exception, StopIteration) as exc:
        raise MobiGoError("MobiGo FAT16 transport partition was not found") from exc
    return "/dev/r" + identifier


def _mac_discover() -> str:
    matches = []
    for block in sorted(glob.glob("/dev/disk[0-9]*")):
        if not re.fullmatch(r"/dev/disk[0-9]+", block):
            continue
        info = _disk_info(block)
        if (
            info.get("MediaName") == DEVICE_MODEL
            and info.get("BusProtocol") == "USB"
            and not info.get("Internal", False)
        ):
            matches.append(block)
    if len(matches) != 1:
        if not matches:
            raise MobiGoError("connected MobiGo 2 was not found")
        raise MobiGoError("multiple MobiGo devices found; use --device")
    return matches[0]


def _windows_discover() -> str:
    script = r"""
$disk = Get-CimInstance Win32_DiskDrive | Where-Object {
  $_.PNPDeviceID -match 'VID_0F88&PID_2D40' -or
  $_.PNPDeviceID -match 'USBSTOR\\DISK&VEN_VTECH&PROD_USB-MSDC_DISK_A' -or
  $_.Model -like 'VTECH USB-MSDC DISK A*'
} | Select-Object -First 1
if ($disk) {
  $parts = Get-CimAssociatedInstance $disk -Association Win32_DiskDriveToDiskPartition
  $logical = foreach ($part in $parts) {
    Get-CimAssociatedInstance $part -Association Win32_LogicalDiskToPartition
  }
  $logical | Select-Object -First 1 -ExpandProperty DeviceID
}
"""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )
    drive = result.stdout.strip().splitlines()
    if result.returncode or not drive:
        raise MobiGoError("connected MobiGo 2 was not found")
    return rf"\\.\{drive[-1].strip()}"


class DeviceSession(AbstractContextManager[MobiGoFS]):
    def __init__(self, device: str | None = None):
        self.requested_device = device
        self.block: str | None = None
        self.backend: _PosixBackend | _WindowsBackend | None = None

    def __enter__(self) -> MobiGoFS:
        if sys.platform == "darwin":
            block = self.requested_device or _mac_discover()
            match = re.fullmatch(r"/dev/r?disk([0-9]+)(?:s[0-9]+)?", block)
            if not match:
                raise MobiGoError("--device must look like /dev/disk5")
            self.block = "/dev/disk" + match.group(1)
            if _disk_info(self.block).get("MediaName") != DEVICE_MODEL:
                raise MobiGoError(f"refusing non-MobiGo disk {self.block}")
            raw = _mac_transport_partition(self.block)
            result = subprocess.run(
                ["diskutil", "unmountDisk", self.block],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                raise MobiGoError(result.stdout.strip() or "could not unmount MobiGo")
            try:
                self.backend = _PosixBackend(raw)
                return MobiGoFS(MailboxTransport(self.backend))
            except Exception:
                if self.backend is not None:
                    self.backend.close()
                    self.backend = None
                subprocess.run(
                    ["diskutil", "mountDisk", self.block],
                    capture_output=True,
                    check=False,
                )
                self.block = None
                raise
        elif os.name == "nt":
            target = self.requested_device or _windows_discover()
            try:
                self.backend = _WindowsBackend(target)
                return MobiGoFS(MailboxTransport(self.backend))
            except Exception:
                if self.backend is not None:
                    self.backend.close()
                    self.backend = None
                raise
        else:
            raise MobiGoError("USB scripts support macOS and Windows")

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.backend is not None:
            self.backend.close()
        if self.block is not None:
            result = subprocess.run(
                ["diskutil", "mountDisk", self.block],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                print(
                    "warning: diskutil could not remount the MobiGo; reconnect it",
                    file=sys.stderr,
                )


def format_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB"]
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f} {unit}" if unit != "B" else f"{value} B"
        amount /= 1024
    return f"{value} B"
