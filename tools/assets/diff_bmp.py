#!/usr/bin/env python3
import argparse
import struct
from pathlib import Path


def load_bmp(path: Path):
    data = path.read_bytes()
    if not data.startswith(b"BM"):
        raise ValueError(f"{path}: not a BMP")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    raw_height = struct.unpack_from("<i", data, 22)[0]
    bits = struct.unpack_from("<H", data, 28)[0]
    if bits != 32:
        raise ValueError(f"{path}: expected 32 bpp, got {bits}")
    height = abs(raw_height)
    top_down = raw_height < 0
    row_bytes = width * 4
    def pixel(x, y):
        source_y = y if top_down else height - 1 - y
        start = pixel_offset + source_y * row_bytes + x * 4
        blue, green, red, alpha = data[start:start+4]
        return red, green, blue
    return width, height, pixel

parser = argparse.ArgumentParser()
parser.add_argument("before", type=Path)
parser.add_argument("after", type=Path)
args = parser.parse_args()
w0,h0,p0=load_bmp(args.before)
w1,h1,p1=load_bmp(args.after)
if (w0,h0)!=(w1,h1):
    raise SystemExit("frame sizes differ")
changed=[]
for y in range(h0):
    for x in range(w0):
        a=p0(x,y); b=p1(x,y)
        if a!=b:
            changed.append((x,y,a,b))
print(f"changed={len(changed)}")
if not changed:
    raise SystemExit(0)
x0=min(x for x,y,a,b in changed); x1=max(x for x,y,a,b in changed)
y0=min(y for x,y,a,b in changed); y1=max(y for x,y,a,b in changed)
print(f"bbox={x0},{y0}..{x1},{y1} size={x1-x0+1}x{y1-y0+1}")
for y in range(y0,y1+1):
    row=[]
    for x in range(x0,x1+1):
        row.append("#" if p0(x,y)!=p1(x,y) else ".")
    print(f"{y:03d} {''.join(row)}")
