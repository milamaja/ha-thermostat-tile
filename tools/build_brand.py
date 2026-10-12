#!/usr/bin/env python3
"""Build the integration's brand icons (custom_components/thermostat_tile/brand/).

A round thermostat with a dial track and a green "eco" badge with a leaf in
the bottom-right corner, drawn with plain Python (no image libraries), in two
colour sets:

    icon.png / icon@2x.png            light theme
    dark_icon.png / dark_icon@2x.png  dark theme

    python tools/build_brand.py
"""
import math
import pathlib
import struct
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "custom_components" / "thermostat_tile" / "brand"

SIZE = 512  # @2x; the 1x icon is this halved
SAMPLES = 3  # per axis, for anti-aliasing

COLOURS = {
    "light": {"body": (255, 152, 0), "track": (255, 224, 178), "knob": (255, 255, 255), "badge": (76, 175, 80), "leaf": (255, 255, 255)},
    "dark": {"body": (255, 167, 38), "track": (120, 72, 0), "knob": (38, 50, 56), "badge": (102, 187, 106), "leaf": (38, 50, 56)},
}

DIAL, DIAL_R = (224, 224), 196
TRACK_R0, TRACK_R1 = 118, 150  # the ring of the dial
OPEN = 90  # degrees of the opening at the bottom of the track
KNOB_ANGLE, KNOB_R = 320, 26  # where the setting is, in degrees (0 = right, clockwise)
BADGE, BADGE_R, BADGE_GAP = (392, 392), 100, 18


def _in_leaf(x, y):
    """A leaf pointing to the top right: the lens between two circles, with a stalk."""
    bx, by = BADGE
    k, r = 26, 70  # circle centres at +-k across the axis, radius r: a wide lens
    u = ((x - bx) - (y - by)) / math.sqrt(2)  # along the axis (bottom-left to top-right)
    v = ((x - bx) + (y - by)) / math.sqrt(2)  # across it
    if math.hypot(u, v - k) <= r and math.hypot(u, v + k) <= r:
        # Midrib: a thin line along the leaf's axis, not to the tip.
        return not (abs(v) <= 3 and -50 < u < 36)
    # Stem at the bottom-left tip.
    return -88 <= u <= -60 and abs(v) <= 5


def _colour_at(x, y, c):
    bx, by = BADGE
    d_badge = math.hypot(x - bx, y - by)
    if d_badge <= BADGE_R:
        return (c["leaf"] if _in_leaf(x, y) else c["badge"]) + (255,)
    if d_badge <= BADGE_R + BADGE_GAP:
        return (0, 0, 0, 0)
    gx, gy = DIAL
    d = math.hypot(x - gx, y - gy)
    if d > DIAL_R:
        return (0, 0, 0, 0)
    kx = gx + (TRACK_R0 + TRACK_R1) / 2 * math.cos(math.radians(KNOB_ANGLE))
    ky = gy + (TRACK_R0 + TRACK_R1) / 2 * math.sin(math.radians(KNOB_ANGLE))
    if math.hypot(x - kx, y - ky) <= KNOB_R:
        return c["knob"] + (255,)
    angle = math.degrees(math.atan2(y - gy, x - gx)) % 360  # 0 = right, 90 = down
    if TRACK_R0 <= d <= TRACK_R1 and abs(angle - 90) > OPEN / 2:
        return c["track"] + (255,)
    return c["body"] + (255,)


def render(c):
    rows, step, n = [], 1 / SAMPLES, SAMPLES * SAMPLES
    for py in range(SIZE):
        row = []
        for px in range(SIZE):
            r = g = b = a = 0
            for sy in range(SAMPLES):
                for sx in range(SAMPLES):
                    cr, cg, cb, ca = _colour_at(px + (sx + 0.5) * step, py + (sy + 0.5) * step, c)
                    r += cr * ca
                    g += cg * ca
                    b += cb * ca
                    a += ca
            row.append((r / n, g / n, b / n, a / n))
        rows.append(row)
    return rows


def halve(rows):
    return [
        [tuple(sum(p[i] for p in (rows[y][x], rows[y][x + 1], rows[y + 1][x], rows[y + 1][x + 1])) / 4 for i in range(4))
         for x in range(0, len(rows[0]), 2)]
        for y in range(0, len(rows), 2)
    ]


def write_png(path, rows):
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for r, g, b, a in row:
            raw += bytes((round(r / a), round(g / a), round(b / a), round(a))) if a else b"\0\0\0\0"

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", len(rows[0]), len(rows), 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for theme, colours in COLOURS.items():
        prefix = "" if theme == "light" else "dark_"
        big = render(colours)
        write_png(OUT / f"{prefix}icon@2x.png", big)
        write_png(OUT / f"{prefix}icon.png", halve(big))
        print(f"{theme}: {prefix}icon.png, {prefix}icon@2x.png")


if __name__ == "__main__":
    main()
