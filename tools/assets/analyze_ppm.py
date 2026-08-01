#!/usr/bin/env python3
from collections import Counter
from pathlib import Path
import argparse
import struct

parser = argparse.ArgumentParser()
parser.add_argument("ppm", type=Path)
parser.add_argument("--x0", type=int, default=0)
parser.add_argument("--y0", type=int, default=0)
parser.add_argument("--x1", type=int)
parser.add_argument("--y1", type=int)
args = parser.parse_args()

data = args.ppm.read_bytes()
if data.startswith(b"P6\n"):
    header, dims, maxval, pixels = data.split(b"\n", 3)
    width, height = map(int, dims.split())
    if maxval != b"255":
        raise SystemExit("expected max value 255")
    def get_pixel(x, y):
        start = (y * width + x) * 3
        return tuple(pixels[start : start + 3])
elif data.startswith(b"BM"):
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    raw_height = struct.unpack_from("<i", data, 22)[0]
    bits = struct.unpack_from("<H", data, 28)[0]
    if bits != 32:
        raise SystemExit(f"expected 32-bit BMP, found {bits}")
    height = abs(raw_height)
    top_down = raw_height < 0
    row_bytes = width * 4
    def get_pixel(x, y):
        source_y = y if top_down else height - 1 - y
        start = pixel_offset + source_y * row_bytes + x * 4
        blue, green, red, alpha = data[start : start + 4]
        return (red, green, blue)
else:
    raise SystemExit("expected binary P6 PPM or 32-bit BMP")

colors = Counter(get_pixel(x, y) for y in range(height) for x in range(width))
background = colors.most_common(1)[0][0]
points = []
for y in range(height):
    for x in range(width):
        rgb = get_pixel(x, y)
        if rgb != background:
            points.append((x, y, rgb))
print(f"size={width}x{height} colors={len(colors)} background={background} nonbackground={len(points)}")
print("top_colors=" + repr(colors.most_common(12)))
if points:
    print("bbox=%d,%d..%d,%d" % (
        min(p[0] for p in points), min(p[1] for p in points),
        max(p[0] for p in points), max(p[1] for p in points)))

x0 = max(0, args.x0)
y0 = max(0, args.y0)
x1 = min(width, args.x1 if args.x1 is not None else width)
y1 = min(height, args.y1 if args.y1 is not None else height)
for y in range(y0, y1):
    row = []
    for x in range(x0, x1):
        rgb = get_pixel(x, y)
        row.append("#" if rgb != background else ".")
    print(f"{y:03d} {''.join(row)}")
