#!/usr/bin/env python3
"""Flatten an S37 image between two unSP word addresses."""

import sys
from pathlib import Path


source = Path(sys.argv[1])
output = Path(sys.argv[2])
base = int(sys.argv[3], 0) * 2
limit = int(sys.argv[4], 0) * 2
memory = {}

for line in source.read_text().splitlines():
    line = line.strip()
    if not line.startswith("S3"):
        continue
    raw = bytes.fromhex(line[2:])
    count = raw[0]
    address = int.from_bytes(raw[1:5], "big")
    data = raw[5:count]
    for offset, value in enumerate(data):
        absolute = address + offset
        if absolute < base:
            raise SystemExit(f"record below image base: {absolute:#x}")
        if absolute < limit:
            memory[absolute] = value

if not memory:
    raise SystemExit("S37 contained no payload records")
end = max(memory) + 1
image = bytearray(b"\xff" * (end - base))
for address, value in memory.items():
    image[address - base] = value
if len(image) & 1:
    image.append(0xff)
output.write_bytes(image)
print(f"program_bytes={len(image)}")
