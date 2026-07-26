#!/usr/bin/env python3
"""Flatten an S37 file into an image based at a requested unSP word address."""
import sys
from pathlib import Path

base_word = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x50000
base = base_word * 2
limit = int(sys.argv[4], 0) * 2 if len(sys.argv) > 4 else None
memory = {}
for line in Path(sys.argv[1]).read_text().splitlines():
    line = line.strip()
    if not line.startswith("S3"):
        continue
    raw = bytes.fromhex(line[2:])
    count = raw[0]
    address = int.from_bytes(raw[1:5], "big")
    data = raw[5:count]
    for i, value in enumerate(data):
        if address + i < base:
            raise SystemExit(f"record below cartridge base: {address+i:#x}")
        if limit is not None and address + i >= limit:
            continue
        memory[address + i] = value
end = max(memory) + 1
image = bytearray(b"\xff" * (end - base))
for address, value in memory.items():
    image[address - base] = value
if len(image) & 1:
    image.append(0xff)
Path(sys.argv[2]).write_bytes(image)
print(f"program_bytes={len(image)}")
