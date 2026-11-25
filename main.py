#!/usr/bin/env python3
"""news-image-20261125: draw one 1024x1024 PNG summing up the world news
of Wednesday 25 November 2026. Python 3.13, standard library only.

Layout (after the winning pattern of the 20261121/22 top-10 entries):
masthead + giant serif date + subhead, 6-number stat strip, region bar,
3 feature panels with drawn scenes, 10 medium cards, world map with
numbered pins + 22-item also-list, DATE CHECK box, footer.
All drawing is vector + bitmap text from an embedded DejaVu Serif blob
(fontdata.py); no Pillow, no network, deterministic.
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fontdata

W = 1024
H = 1024
PAPER = (246, 241, 229)
INK = (22, 21, 19)
RED = (164, 31, 31)
DARKRED = (122, 20, 20)
BLUE = (31, 78, 121)
GOLD = (176, 141, 26)
GREEN = (46, 125, 50)
PURPLE = (106, 61, 154)
SLATE = (84, 110, 122)
TEAL = (0, 131, 143)
MUTED = (107, 100, 85)
LINEC = (60, 55, 45)
MAPLAND = (232, 221, 196)
MAPLINE = (138, 127, 99)

REGION_COLORS = {
    "EUROPE": BLUE,
    "ASIA-PACIFIC": GOLD,
    "MIDDLE EAST": RED,
    "AFRICA": GREEN,
    "AMERICAS": PURPLE,
    "GLOBAL": SLATE,
    "OCEANIA": TEAL,
}


# ---------------------------------------------------------------- PNG output
def write_png(path, rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, w * h * 3, 3):
            self.buf[i] = r
            self.buf[i + 1] = g
            self.buf[i + 2] = b
        self.clip = (0, 0, w, h)

    def set_clip(self, x, y, w, h):
        x = max(0, x)
        y = max(0, y)
        self.clip = (x, y, max(0, min(self.w - x, w)), max(0, min(self.h - y, h)))

    def reset_clip(self):
        self.clip = (0, 0, self.w, self.h)

    def px(self, x, y, color):
        cx, cy, cw, ch = self.clip
        if x < cx or x >= cx + cw or y < cy or y >= cy + ch:
            return
        i = (y * self.w + x) * 3
        self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def blend(self, x, y, color, a):
        cx, cy, cw, ch = self.clip
        if x < cx or x >= cx + cw or y < cy or y >= cy + ch or a <= 0.0:
            return
        i = (y * self.w + x) * 3
        if a >= 1.0:
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color
            return
        r, g, b = color
        self.buf[i] = int(r * a + self.buf[i] * (1.0 - a) + 0.5)
        self.buf[i + 1] = int(g * a + self.buf[i + 1] * (1.0 - a) + 0.5)
        self.buf[i + 2] = int(b * a + self.buf[i + 2] * (1.0 - a) + 0.5)

    def fill_rect(self, x, y, w, h, color):
        cx, cy, cw, ch = self.clip
        x0 = max(x, cx)
        y0 = max(y, cy)
        x1 = min(x + w, cx + cw)
        y1 = min(y + h, cy + ch)
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            span = (x1 - x0) * 3
            row = bytes((r, g, b)) * (x1 - x0)
            self.buf[base:base + span] = row

    def outline_rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.fill_rect(x - t // 2, y - t // 2, t, t, color)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            dx = int((r * r - dy * dy) ** 0.5) if r * r - dy * dy >= 0 else 0
            self.fill_rect(cx - dx, yy, dx * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, t=2):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            outer = int((r * r - dy * dy) ** 0.5) if r * r - dy * dy >= 0 else 0
            inner = int(((r - t) ** 2 - dy * dy) ** 0.5) if (r - t) ** 2 - dy * dy >= 0 else 0
            self.fill_rect(cx - outer, yy, outer - inner, 1, color)
            self.fill_rect(cx + inner + 1, yy, outer - inner, 1, color)

    def polygon(self, pts, color):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    if y1 != y0:
                        xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[k]), yy, max(1, int(xs[k + 1]) - int(xs[k])), 1, color)


# ---------------------------------------------------------------- text engine
GLYPHS = fontdata.load()
_CACHE = {}
_UNPACKED = {}


def _unpacked(weight, ch):
    key = (weight, ch)
    if key in _UNPACKED:
        return _UNPACKED[key]
    adv, w, h, xoff, yoff, bits = GLYPHS[weight].get(
        ch, GLYPHS[weight]["?"])
    grid = []
    rowbytes = (w + 7) // 8
    for yy in range(h):
        row = []
        for xx in range(w):
            byte = bits[yy * rowbytes + xx // 8] if yy * rowbytes + xx // 8 < len(bits) else 0
            row.append((byte >> (7 - xx % 8)) & 1)
        grid.append(row)
    val = (adv, w, h, xoff, yoff, grid)
    _UNPACKED[key] = val
    return val


def _scaled(ch, size, bold):
    key = (ch, size, bold)
    if key in _CACHE:
        return _CACHE[key]
    weight = "bold" if bold else "regular"
    adv, w, h, xoff, yoff, grid = _unpacked(weight, ch)
    s = size / float(fontdata.EM)
    tw = max(1, int(round(w * s)))
    th = max(1, int(round(h * s)))
    cov = [[0.0] * tw for _ in range(th)]
    for ty in range(th):
        sy0 = ty / s
        sy1 = (ty + 1) / s
        y0i = int(sy0)
        y1i = min(h, int(sy1) + 1)
        for tx in range(tw):
            sx0 = tx / s
            sx1 = (tx + 1) / s
            x0i = int(sx0)
            x1i = min(w, int(sx1) + 1)
            total = 0.0
            for gy in range(y0i, y1i):
                oy0 = max(sy0, gy)
                oy1 = min(sy1, gy + 1)
                if oy1 <= oy0:
                    continue
                grow = grid[gy]
                for gx in range(x0i, x1i):
                    if not grow[gx]:
                        continue
                    ox0 = max(sx0, gx)
                    ox1 = min(sx1, gx + 1)
                    if ox1 > ox0:
                        total += (ox1 - ox0) * (oy1 - oy0)
            cov[ty][tx] = min(1.0, total * s * s)
    val = (int(round(adv * s)), tw, th, int(round(xoff * s)), int(round(yoff * s)), cov)
    _CACHE[key] = val
    return val


def text_width(s, size, bold=False):
    return sum(_scaled(ch, size, bold)[0] for ch in s)


def draw_text(cv, x, y, s, size, color, bold=False, align="left"):
    """Draw text; y is the top of the ascender line. Returns width used."""
    if align == "center":
        x -= text_width(s, size, bold) // 2
    elif align == "right":
        x -= text_width(s, size, bold)
    cx = x
    for ch in s:
        adv, tw, th, xoff, yoff, cov = _scaled(ch, size, bold)
        for ty in range(th):
            row = cov[ty]
            yy = y + yoff + ty
            for tx in range(tw):
                a = row[tx]
                if a > 0.02:
                    cv.blend(cx + xoff + tx, yy, color, a)
        cx += adv
    return cx - x


def wrap(s, size, bold, width, max_lines=None):
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, size, bold) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and text_width(lines[-1] + "…", size, bold) > width:
            lines[-1] = lines[-1][:-1].rstrip()
        lines[-1] = lines[-1].rstrip() + "…"
    return lines


def draw_lines(cv, x, y, lines, size, color, bold=False, lh=None):
    if lh is None:
        lh = int(size * 1.22)
    for ln in lines:
        draw_text(cv, x, y, ln, size, color, bold)
        y += lh
    return y


# ---------------------------------------------------------------- scenes
# Every scene draws inside box (x, y, w, h) only; the canvas clip is set
# to the box before the scene runs, so nothing can spill over a neighbour.
def _box(x, y, w, h):
    return (x, y, w, h)


def scene_huawei(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (16, 32, 54))
    # circuit traces
    for i in range(5):
        yy = y + int(h * (0.18 + i * 0.16))
        cv.hline(x + int(w * 0.06), yy, int(w * 0.88), (46, 110, 150), 2)
        cv.circle(x + int(w * (0.12 + i * 0.18)), yy, 3, (120, 200, 120))
    # chip
    cx, cy = x + w // 2, y + h // 2
    cw, chh = int(w * 0.42), int(h * 0.52)
    cv.fill_rect(cx - cw // 2, cy - chh // 2, cw, chh, (20, 60, 40))
    cv.outline_rect(cx - cw // 2, cy - chh // 2, cw, chh, (120, 200, 120), 2)
    for i in range(4):
        px = cx - cw // 2 + int(cw * (0.2 + i * 0.2))
        cv.vline(px, cy - chh // 2 - 6, 6, (120, 200, 120), 2)
        cv.vline(px, cy + chh // 2, 6, (120, 200, 120), 2)
    cv.fill_rect(cx - int(cw * 0.22), cy - int(chh * 0.22), int(cw * 0.44), int(chh * 0.44), (200, 60, 60))
    # gavel
    gx, gy = x + int(w * 0.78), y + int(h * 0.72)
    cv.line(gx - 16, gy + 10, gx + 16, gy - 10, (220, 180, 120), 3)
    cv.fill_rect(gx - 4, gy - 16, 14, 8, (220, 180, 120))


def scene_cia(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (24, 24, 30))
    # headquarters block
    bx, by = x + int(w * 0.14), y + int(h * 0.34)
    bw, bh = int(w * 0.72), int(h * 0.5)
    cv.fill_rect(bx, by, bw, bh, (70, 76, 88))
    cv.polygon([(bx - 6, by), (bx + bw // 2, by - int(h * 0.16)), (bx + bw + 6, by)], (96, 102, 116))
    for i in range(5):
        cx = bx + int(bw * (0.12 + i * 0.19))
        cv.fill_rect(cx, by + int(bh * 0.25), int(bw * 0.09), int(bh * 0.6), (24, 24, 30))
    # warning triangle
    tx, ty = x + int(w * 0.72), y + int(h * 0.16)
    tr = int(min(w, h) * 0.16)
    cv.polygon([(tx, ty - tr), (tx + tr, ty + tr), (tx - tr, ty + tr)], (230, 180, 30))
    cv.fill_rect(tx - 1, ty - tr // 2, 3, tr, INK)
    cv.fill_rect(tx - 1, ty + tr // 2, 3, 3, INK)
    # binary rain
    for i, (fx, fy) in enumerate([(0.08, 0.12), (0.2, 0.06), (0.9, 0.3), (0.05, 0.55), (0.93, 0.62)]):
        draw_text(cv, x + int(w * fx), y + int(h * fy), "01" if i % 2 else "10",
                  max(9, int(h * 0.11)), (90, 200, 120), bold=True)


def scene_riyadh(cv, b):
    x, y, w, h = b
    # dusk bands
    cv.fill_rect(x, y, w, int(h * 0.45), (250, 170, 90))
    cv.fill_rect(x, y + int(h * 0.45), w, int(h * 0.3), (220, 110, 60))
    cv.fill_rect(x, y + int(h * 0.75), w, h - int(h * 0.75), (60, 50, 70))
    # tower
    tx = x + int(w * 0.42)
    tw = int(w * 0.16)
    cv.polygon([(tx, y + int(h * 0.92)), (tx, y + int(h * 0.18)),
                (tx + tw // 2, y + int(h * 0.06)), (tx + tw, y + int(h * 0.18)),
                (tx + tw, y + int(h * 0.92))], (40, 40, 55))
    for i in range(5):
        wy = y + int(h * (0.3 + i * 0.12))
        cv.fill_rect(tx + 3, wy, tw - 6, 3, (250, 200, 90))
    # starburst at the tip
    sx, sy = tx + tw // 2, y + int(h * 0.1)
    for ang in range(0, 360, 30):
        import math
        r = int(h * 0.16)
        ex = sx + int(r * math.cos(math.radians(ang)))
        ey = sy + int(r * math.sin(math.radians(ang)))
        cv.line(sx, sy, ex, ey, (255, 220, 80), 3)
    cv.circle(sx, sy, int(h * 0.07), (255, 240, 160))
    # second building + smoke
    cv.fill_rect(x + int(w * 0.66), y + int(h * 0.55), int(w * 0.2), int(h * 0.37), (50, 45, 60))
    cv.circle(x + int(w * 0.3), y + int(h * 0.2), int(h * 0.09), (90, 85, 95))
    cv.circle(x + int(w * 0.24), y + int(h * 0.14), int(h * 0.07), (110, 105, 115))


def scene_putin(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (150, 60, 55))
    # kremlin wall + tower
    cv.fill_rect(x, y + int(h * 0.62), w, int(h * 0.38), (120, 30, 30))
    tx = x + int(w * 0.3)
    cv.fill_rect(tx, y + int(h * 0.3), int(w * 0.16), int(h * 0.62), (140, 40, 40))
    cv.polygon([(tx - 4, y + int(h * 0.3)), (tx + int(w * 0.08), y + int(h * 0.08)),
                (tx + int(w * 0.16) + 4, y + int(h * 0.3))], (40, 120, 60))
    cv.circle(tx + int(w * 0.08), y + int(h * 0.14), 4, (250, 210, 60))
    # oil derrick
    dx = x + int(w * 0.68)
    cv.line(dx, y + int(h * 0.9), dx + int(w * 0.1), y + int(h * 0.35), (40, 30, 25), 3)
    cv.line(dx + int(w * 0.2), y + int(h * 0.9), dx + int(w * 0.1), y + int(h * 0.35), (40, 30, 25), 3)
    cv.line(dx, y + int(h * 0.9), dx + int(w * 0.2), y + int(h * 0.9), (40, 30, 25), 3)
    # flame
    cv.polygon([(dx + int(w * 0.1) - 6, y + int(h * 0.34)), (dx + int(w * 0.1), y + int(h * 0.2)),
                (dx + int(w * 0.1) + 6, y + int(h * 0.34))], (250, 160, 40))


def scene_bunia(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (190, 200, 150))
    cv.polygon([(x, y + int(h * 0.7)), (x + int(w * 0.4), y + int(h * 0.45)),
                (x + int(w * 0.7), y + int(h * 0.75)), (x + w, y + int(h * 0.6)),
                (x + w, y + h), (x, y + h)], (120, 150, 90))
    # tents
    for fx in (0.18, 0.55):
        tx = x + int(w * fx)
        ty = y + int(h * 0.72)
        cv.polygon([(tx, ty - 14), (tx + 16, ty), (tx - 16, ty)], (230, 220, 190))
    # retreat arrows (dashed, pointing left)
    for fy in (0.22, 0.38):
        ay = y + int(h * fy)
        for i in range(4):
            ax = x + int(w * (0.78 - i * 0.13))
            cv.fill_rect(ax, ay, int(w * 0.07), 3, RED)
        cv.polygon([(x + int(w * 0.2), ay - 6), (x + int(w * 0.2), ay + 9),
                    (x + int(w * 0.12), ay + 1)], RED)


def scene_heli(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (170, 205, 225))
    cv.polygon([(x, y + h), (x + int(w * 0.3), y + int(h * 0.55)),
                (x + int(w * 0.6), y + h)], (110, 140, 120))
    cv.polygon([(x + int(w * 0.55), y + h), (x + int(w * 0.8), y + int(h * 0.6)),
                (x + w, y + h)], (90, 120, 105))
    # helicopter
    cx, cy = x + w // 2, y + int(h * 0.4)
    cv.hline(cx - int(w * 0.3), cy - int(h * 0.16), int(w * 0.6), INK, 3)
    cv.circle(cx, cy, int(h * 0.17), (60, 60, 65))
    cv.fill_rect(cx + int(h * 0.1), cy - 2, int(w * 0.26), 5, (60, 60, 65))
    cv.fill_rect(cx - int(w * 0.05), cy + int(h * 0.12), 4, int(h * 0.2), (60, 60, 65))
    # smoke
    cv.circle(x + int(w * 0.82), y + int(h * 0.72), int(h * 0.1), (120, 120, 120))
    cv.circle(x + int(w * 0.86), y + int(h * 0.6), int(h * 0.08), (140, 140, 140))


def scene_boat(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, int(h * 0.55), (200, 225, 240))
    cv.circle(x + int(w * 0.82), y + int(h * 0.18), int(h * 0.11), (250, 210, 90))
    cv.fill_rect(x, y + int(h * 0.55), w, h - int(h * 0.55), (30, 90, 140))
    for i in range(3):
        wy = y + int(h * (0.62 + i * 0.12))
        for k in range(6):
            wx = x + int(w * (0.05 + k * 0.17))
            cv.line(wx, wy, wx + int(w * 0.08), wy - 4, (160, 200, 230), 2)
    # boat
    bx, by = x + int(w * 0.3), y + int(h * 0.52)
    cv.polygon([(bx, by), (bx + int(w * 0.34), by), (bx + int(w * 0.28), by + int(h * 0.14)),
                (bx + int(w * 0.06), by + int(h * 0.14))], (120, 70, 40))
    cv.vline(bx + int(w * 0.17), by - int(h * 0.24), int(h * 0.24), (80, 50, 30), 2)
    cv.polygon([(bx + int(w * 0.17), by - int(h * 0.24)), (bx + int(w * 0.17), by - 2),
                (bx + int(w * 0.3), by - 2)], (240, 240, 240))
    # lifebuoy
    cv.ring(x + int(w * 0.78), y + int(h * 0.72), int(h * 0.1), (230, 60, 40), 4)


def scene_nikkei(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (245, 240, 225))
    # axes
    cv.vline(x + int(w * 0.1), y + int(h * 0.12), int(h * 0.72), INK, 2)
    cv.hline(x + int(w * 0.1), y + int(h * 0.84), int(w * 0.82), INK, 2)
    # falling candles
    for i in range(5):
        cx = x + int(w * (0.2 + i * 0.15))
        top = y + int(h * (0.2 + i * 0.11))
        bot = top + int(h * 0.16)
        cv.fill_rect(cx - 4, top, 8, bot - top, (200, 40, 40))
        cv.vline(cx, top - 6, bot - top + 12, (200, 40, 40), 2)
    # down arrow
    ax, ay = x + int(w * 0.82), y + int(h * 0.2)
    cv.line(ax - 8, ay - 10, ax, ay + 12, RED, 4)
    cv.line(ax + 8, ay - 10, ax, ay + 12, RED, 4)


def scene_madrid(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (40, 130, 70))
    for i in range(4):
        cv.fill_rect(x + int(w * i * 0.25), y, int(w * 0.25), h,
                     (46, 140, 76) if i % 2 else (40, 130, 70))
    # goal
    gx, gy = x + int(w * 0.62), y + int(h * 0.3)
    cv.outline_rect(gx, gy, int(w * 0.3), int(h * 0.42), (240, 240, 240), 3)
    cv.vline(gx + int(w * 0.15), gy, int(h * 0.42), (240, 240, 240), 1)
    # ball
    cv.circle(x + int(w * 0.3), y + int(h * 0.62), int(h * 0.16), (245, 245, 245))
    cv.circle(x + int(w * 0.3), y + int(h * 0.62), int(h * 0.06), INK)
    # scoreboard
    sw, sh = int(w * 0.34), int(h * 0.3)
    cv.fill_rect(x + int(w * 0.05), y + int(h * 0.06), sw, sh, INK)
    draw_text(cv, x + int(w * 0.05) + sw // 2, y + int(h * 0.06) + 2, "5-1",
              max(12, int(sh * 0.62)), (255, 255, 255), bold=True, align="center")


def scene_who(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (225, 235, 240))
    # hospital
    bx, by = x + int(w * 0.12), y + int(h * 0.3)
    bw, bh = int(w * 0.5), int(h * 0.55)
    cv.fill_rect(bx, by, bw, bh, (250, 250, 250))
    cv.outline_rect(bx, by, bw, bh, (120, 140, 150), 2)
    for i in range(3):
        cv.fill_rect(bx + int(bw * (0.15 + i * 0.3)), by + int(bh * 0.2),
                     int(bw * 0.16), int(bh * 0.25), (120, 170, 200))
    # red cross sign
    cx, cy = bx + bw // 2, by - int(h * 0.08)
    cv.fill_rect(cx - 3, cy - 10, 6, 20, RED)
    cv.fill_rect(cx - 10, cy - 3, 20, 6, RED)
    # van
    vx, vy = x + int(w * 0.66), y + int(h * 0.66)
    cv.fill_rect(vx, vy, int(w * 0.26), int(h * 0.18), (240, 240, 240))
    cv.outline_rect(vx, vy, int(w * 0.26), int(h * 0.18), INK, 1)
    cv.circle(vx + int(w * 0.06), vy + int(h * 0.18), 4, INK)
    cv.circle(vx + int(w * 0.2), vy + int(h * 0.18), 4, INK)


def scene_iraq(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, int(h * 0.6), (250, 210, 140))
    cv.circle(x + int(w * 0.8), y + int(h * 0.16), int(h * 0.12), (250, 180, 60))
    cv.fill_rect(x, y + int(h * 0.6), w, h - int(h * 0.6), (210, 170, 110))
    # pumpjack
    px, py = x + int(w * 0.3), y + int(h * 0.72)
    cv.line(px, py, px + int(w * 0.05), py - int(h * 0.34), INK, 3)
    cv.line(px + int(w * 0.3), py, px + int(w * 0.05), py - int(h * 0.34), INK, 3)
    cv.line(px - int(w * 0.12), py - int(h * 0.3), px + int(w * 0.24), py - int(h * 0.4), INK, 4)
    cv.fill_rect(px + int(w * 0.2), py - int(h * 0.4), 5, int(h * 0.14), INK)
    # derrick
    dx = x + int(w * 0.72)
    cv.line(dx, y + h, dx + int(w * 0.05), y + int(h * 0.4), (60, 50, 40), 3)
    cv.line(dx + int(w * 0.12), y + h, dx + int(w * 0.05), y + int(h * 0.4), (60, 50, 40), 3)


def scene_wardead(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (35, 35, 45))
    for r in range(3):
        for c in range(6):
            cx = x + int(w * (0.12 + c * 0.15))
            cy = y + int(h * (0.24 + r * 0.26))
            cv.fill_rect(cx - 1, cy - 7, 3, 14, (220, 220, 220))
            cv.fill_rect(cx - 6, cy - 3, 12, 3, (220, 220, 220))
    # candle flames
    for fx in (0.2, 0.5, 0.8):
        fx0 = x + int(w * fx)
        fy0 = y + int(h * 0.86)
        cv.fill_rect(fx0 - 1, fy0 - 6, 3, 6, (240, 240, 240))
        cv.polygon([(fx0 - 3, fy0 - 6), (fx0, fy0 - 14), (fx0 + 3, fy0 - 6)], (250, 180, 60))


def scene_jakarta(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (200, 225, 235))
    # parliament dome
    bx, by = x + int(w * 0.2), y + int(h * 0.5)
    bw = int(w * 0.6)
    cv.fill_rect(bx, by, bw, int(h * 0.4), (200, 190, 160))
    cv.polygon([(bx - 4, by), (bx + bw // 2, by - int(h * 0.3)),
                (bx + bw + 4, by)], (180, 60, 60))
    cv.circle(bx + bw // 2, by - int(h * 0.3), 4, (250, 210, 60))
    # flag
    fx = x + int(w * 0.82)
    cv.vline(fx, y + int(h * 0.2), int(h * 0.55), INK, 2)
    cv.fill_rect(fx, y + int(h * 0.2), int(w * 0.12), int(h * 0.1), RED)
    cv.fill_rect(fx, y + int(h * 0.3), int(w * 0.12), int(h * 0.1), (250, 250, 250))
    # resignation letter
    lx, ly = x + int(w * 0.06), y + int(h * 0.62)
    cv.fill_rect(lx, ly, int(w * 0.16), int(h * 0.26), (255, 255, 255))
    cv.outline_rect(lx, ly, int(w * 0.16), int(h * 0.26), INK, 1)
    for i in range(3):
        cv.hline(lx + 3, ly + 5 + i * 5, int(w * 0.16) - 6, MUTED, 1)


def scene_megaspeed(cv, b):
    x, y, w, h = b
    cv.fill_rect(x, y, w, h, (20, 40, 60))
    cx, cy = x + w // 2, y + h // 2
    cw, chh = int(w * 0.4), int(h * 0.5)
    cv.fill_rect(cx - cw // 2, cy - chh // 2, cw, chh, (30, 90, 60))
    cv.outline_rect(cx - cw // 2, cy - chh // 2, cw, chh, (120, 200, 120), 2)
    for i in range(3):
        px = cx - cw // 2 + int(cw * (0.25 + i * 0.25))
        cv.vline(px, cy - chh // 2 - 5, 5, (120, 200, 120), 2)
        cv.vline(px, cy + chh // 2, 5, (120, 200, 120), 2)
    # prohibition ring
    r = int(min(w, h) * 0.3)
    cv.ring(cx, cy, r, RED, 4)
    cv.line(cx - r + 4, cy + r - 4, cx + r - 4, cy - r + 4, RED, 4)


SCENES = {
    "huawei": scene_huawei, "cia": scene_cia, "riyadh": scene_riyadh,
    "putin": scene_putin, "bunia": scene_bunia, "heli": scene_heli,
    "boat": scene_boat, "nikkei": scene_nikkei, "madrid": scene_madrid,
    "who": scene_who, "iraq": scene_iraq, "wardead": scene_wardead,
    "jakarta": scene_jakarta, "megaspeed": scene_megaspeed,
}


# ---------------------------------------------------------------- world map
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 62), (-60, 55), (-55, 47), (-65, 45), (-75, 35), (-80, 25),
     (-90, 21), (-97, 16), (-105, 20), (-115, 28), (-125, 40), (-125, 49),
     (-140, 60), (-155, 58), (-165, 60)],
    [(-80, 10), (-75, 5), (-60, 0), (-50, -5), (-35, -8), (-40, -20),
     (-50, -30), (-58, -38), (-65, -45), (-70, -52), (-73, -40), (-75, -25),
     (-80, -15), (-80, -5)],
    [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (32, 31), (35, 28),
     (43, 12), (51, 11), (48, 0), (40, -10), (35, -20), (30, -30), (20, -35),
     (15, -28), (12, -18), (13, -10), (9, 4), (-8, 5), (-15, 11)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (25, 65), (20, 70),
     (15, 70), (10, 68), (5, 60), (0, 55), (-5, 50), (-10, 45)],
    [(30, 62), (40, 68), (55, 72), (70, 73), (90, 75), (110, 76), (130, 72),
     (150, 70), (170, 66), (178, 65), (170, 60), (160, 55), (150, 45),
     (140, 40), (135, 35), (130, 32), (127, 35), (122, 38), (120, 30),
     (115, 22), (108, 15), (105, 10), (100, 8), (97, 15), (95, 20),
     (90, 22), (85, 20), (80, 15), (75, 8), (72, 20), (68, 25), (62, 25),
     (57, 27), (52, 29), (48, 30), (44, 29), (40, 32), (36, 36), (32, 38),
     (28, 40), (26, 40)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (129, -32), (135, -35),
     (140, -38), (145, -38), (150, -37), (153, -32), (150, -25), (146, -19),
     (142, -11), (137, -12), (135, -15), (132, -12), (130, -13), (126, -14),
     (122, -17), (118, -20)],
]

# (story number, lon, lat, region, tag dx, tag dy)
PINS = [
    (1, -74.0, 40.7, "GLOBAL", 9, -13),
    (2, -77.0, 38.9, "AMERICAS", -26, 4),
    (3, 46.7, 24.6, "MIDDLE EAST", 9, -13),
    (4, 37.6, 55.8, "EUROPE", 16, -22),
    (5, 30.2, 1.6, "AFRICA", 9, -13),
    (6, 30.5, 39.8, "EUROPE", 9, -13),
    (7, -17.4, 14.7, "AFRICA", 9, -13),
    (8, 139.7, 35.7, "ASIA-PACIFIC", 9, -13),
    (9, -3.7, 40.4, "EUROPE", -26, -13),
    (10, 29.5, 1.5, "AFRICA", -26, 4),
    (11, 44.4, 35.5, "MIDDLE EAST", 9, 4),
    (12, 30.5, 50.4, "EUROPE", -32, 6),
    (13, 106.8, -6.2, "ASIA-PACIFIC", 9, -13),
]


def draw_map(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (214, 228, 236))
    cv.outline_rect(x, y, w, h, LINEC, 1)
    lon0, lon1, lat0, lat1 = -170.0, 190.0, 75.0, -58.0

    def proj(lon, lat):
        px = x + int((lon - lon0) / (lon1 - lon0) * w)
        py = y + int((lat0 - lat) / (lat0 - lat1) * h)
        return px, py

    for cont in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in cont]
        cv.polygon(pts, MAPLAND)
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            cv.line(x0, y0, x1, y1, MAPLINE, 1)
    # pins with leader lines to a small number tag
    for num, lon, lat, region, tdx, tdy in PINS:
        px, py = proj(lon, lat)
        color = REGION_COLORS[region]
        cv.circle(px, py, 6, color)
        cv.ring(px, py, 6, INK, 1)
        # leader line to the tag
        tx, ty = px + tdx, py + tdy
        cv.line(px + (5 if tdx > 0 else -5), py - 5, tx, ty, INK, 1)
        cv.fill_rect(tx - 1, ty - 7, 15, 13, (255, 255, 255))
        cv.outline_rect(tx - 1, ty - 7, 15, 13, INK, 1)
        draw_text(cv, tx + 1, ty - 7, str(num), 10, INK, bold=True)


# ---------------------------------------------------------------- content
FEATURES = [
    dict(n=1, region="GLOBAL", scene="huawei", kicker="HUAWEI: GUILTY",
         loc="1 — NEW YORK — GLOBAL",
         head="Huawei found guilty of stealing trade secrets",
         body="A New York jury found the Chinese tech giant guilty on 10 of 12 counts, including trade-secret theft. Huawei rejects the verdict.",
         src="US Justice Dept / AFP · FT · Reuters"),
    dict(n=2, region="AMERICAS", scene="cia", kicker="WASHINGTON: CYBERATTACK",
         loc="2 — WASHINGTON — AMERICAS",
         head="CIA and spy chief's office hit by cyberattack",
         body="CNN reports the CIA and the spy chief's office were hit by hackers. Unclassified systems were affected.",
         src="CNN · Daily Sabah · VNA"),
    dict(n=3, region="MIDDLE EAST", scene="riyadh", kicker="RIYADH: MISSILE STRIKE",
         loc="3 — RIYADH — MIDDLE EAST",
         head="Houthi missile hits Riyadh's tallest tower",
         body="A Houthi missile struck the capital's tallest tower, wounding 11, Saudi Civil Defense said — the latest strike to reach Riyadh.",
         src="Daily Sabah · Reuters"),
]

MEDIUMS = [
    dict(n=4, region="EUROPE", scene="putin", kicker="MOSCOW: WARNING",
         head="Putin: retaliation 'inevitable'",
         body="Putin warns of retaliation as Kyiv keeps hitting refineries.",
         src="WireMinute · Reuters"),
    dict(n=5, region="AFRICA", scene="bunia", kicker="BUNIA: REBELS PULL BACK",
         head="DR Congo rebels halt Bunia advance",
         body="Rebels halt the Bunia advance and pull back.",
         src="WireMinute · Starlit Daily"),
    dict(n=6, region="EUROPE", scene="heli", kicker="ESKISEHIR: CRASH",
         head="Turkish helicopter crash kills five",
         body="Five soldiers die in a training-flight helicopter crash.",
         src="WireMinute · Daily Sabah"),
    dict(n=7, region="AFRICA", scene="boat", kicker="DAKAR: BOAT LOST",
         head="175 migrants missing off Senegal",
         body="About 175 migrants are missing after a boat vanishes at sea.",
         src="WireMinute · Reuters"),
    dict(n=8, region="ASIA-PACIFIC", scene="nikkei", kicker="TOKYO: MARKETS",
         head="Nikkei dives 1,600 points",
         body="Tokyo shares plunge at one stage as the AI sell-off rolls on.",
         src="TV Asahi · BBN Times"),
    dict(n=9, region="EUROPE", scene="madrid", kicker="MADRID: 5-1 COMEBACK",
         head="Real Madrid roar back, win 5-1",
         body="Bellingham stunner, Mbappe brace: 5-1 over PSV.",
         src="Reuters · UEFA"),
    dict(n=10, region="AFRICA", scene="who", kicker="ITURI: EBOLA",
         head="WHO pulls staff from Ebola hospital",
         body="WHO staff leave the Akwe hospital after three days sheltering.",
         src="VNA · Reuters"),
    dict(n=11, region="MIDDLE EAST", scene="iraq", kicker="BAGHDAD: OILFIELDS",
         head="Iraq orders seizure of Kurdish oilfields",
         body="Federal forces told to seize oilfields and crossings.",
         src="Starlit Daily · Reuters"),
    dict(n=12, region="EUROPE", scene="wardead", kicker="MOSCOW: WAR DEAD",
         head="Russian war dead put at 720,000",
         body="Leaked records put the war dead at 720,000.",
         src="WireMinute · RFE/RL"),
    dict(n=13, region="ASIA-PACIFIC", scene="jakarta", kicker="JAKARTA: RESIGNS",
         head="Indonesia's Vice-President resigns",
         body="The Vice-President resigns amid political strain.",
         src="Starlit Daily · Reuters"),
]

ALSO = [
    (14, "US blacklists Megaspeed over Nvidia chips"),
    (15, "Zelenskiy confirms strike on Russian ship"),
    (16, "Sarkozy and Bruni ordered to face trial"),
    (17, "NATO plans early-warning jets for Poland"),
    (18, "GPS jamming disrupts 140 UK flights"),
    (19, "Arsenal 1-1 Dortmund; Man City 2-2 Napoli"),
    (20, "Denmark upholds 'ghetto' evictions"),
    (21, "Israel: Iran building chemical weapons"),
    (22, "Iran's pharmacies run dry"),
    (23, "Houthis 'won't seize Aden', army says"),
    (24, "Israeli strikes hit south Lebanon"),
    (25, "Senegal's AFCON title restored by CAS"),
    (26, "Nigerian emir suspended"),
    (27, "Cameroon separatist faces Norway court"),
    (28, "BJP and Akali Dal reunite for Punjab 2027"),
    (29, "5.6 quake hits Nepal's Koshi Province"),
    (30, "Xiamen Air orders 50 Boeing 737-8s"),
    (31, "Malaysia to send Rohingya back to Myanmar"),
    (32, "Fiji declares emergency over El Nino drought"),
    (33, "Trump pardons turkeys Freedom and Feathers"),
    (34, "Giuliani awarded Medal of Freedom"),
    (35, "Virginia, Oregon sue SpaceX over Grok"),
]

STATS = [
    ("720,000", "Russian soldiers killed, leaked records say"),
    ("175", "migrants missing after Senegal boat vanishes"),
    ("11", "wounded in the Riyadh tower strike"),
    ("5", "killed in the Turkish helicopter crash"),
    ("1,600", "points, the Nikkei's intraday fall"),
    ("50", "Boeing jets ordered by Xiamen Air"),
]

REGIONS = [("EUROPE", 10), ("ASIA-PACIFIC", 6), ("MIDDLE EAST", 6),
           ("AFRICA", 6), ("AMERICAS", 4), ("GLOBAL", 2), ("OCEANIA", 1)]

DATE_CHECK = (
    "Left out as earlier news: Tuesday's Asia chip rally (Nikkei +3.91%, KOSPI +6%, "
    "Taiex +9%) — that trading day was 24 November. The Real Madrid–PSV match was "
    "played Tuesday evening in Europe but ended on Wednesday in Asian time zones; the "
    "Huawei verdict was handed down Tuesday in New York and reported worldwide on "
    "25 November. Not confirmed when drawn, so not shown: the final toll from the "
    "missing Senegal boat; the full scope of the CIA/ODNI breach. The Nikkei's "
    "1,600-point fall is the 25 November session, not the 24 November close."
)


# ---------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)
    x0, x1 = 18, 1006
    cw = x1 - x0

    # masthead
    draw_text(cv, x0, 12, "THE WORLD IN ONE DAY", 15, RED, bold=True)
    draw_text(cv, x1, 14, "35 STORIES · 7 REGIONS · AS REPORTED ON WEDNESDAY 25 NOVEMBER 2026",
              12, MUTED, align="right")
    cv.hline(x0, 34, cw, INK, 2)
    cv.hline(x0, 37, cw, RED, 1)

    # giant date headline
    draw_text(cv, W // 2, 44, "Wednesday 25 November 2026", 56, INK, bold=True, align="center")
    draw_text(cv, W // 2, 104,
              "Huawei guilty on 10 counts · CIA and spy chief's office hit by hackers · Houthi missile strikes Riyadh's tallest tower",
              16, INK, align="center")

    # stat strip
    y = 130
    cv.hline(x0, y, cw, INK, 1)
    cell = cw // 6
    for i, (num, cap) in enumerate(STATS):
        cx = x0 + i * cell
        if i:
            cv.vline(cx, y + 4, 50, MUTED, 1)
        draw_text(cv, cx + cell // 2, y + 4, num, 28, RED, bold=True, align="center")
        lines = wrap(cap, 11, False, cell - 12, max_lines=2)
        draw_lines(cv, cx + 6, y + 34, lines, 11, INK, lh=12)
    cv.hline(x0, y + 58, cw, INK, 1)

    # region bar
    y = 198
    total_w = 0
    chips = []
    for name, count in REGIONS:
        label = "%s %d" % (name, count)
        wch = text_width(label, 12, True) + 22
        chips.append((name, count, label, wch))
        total_w += wch
    gap = (cw - total_w) // (len(chips) - 1)
    cx = x0
    for name, count, label, wch in chips:
        cv.fill_rect(cx, y, wch, 22, REGION_COLORS[name])
        draw_text(cv, cx + wch // 2, y + 4, label, 12, (255, 255, 255), bold=True, align="center")
        cx += wch + gap

    # features
    y = 226
    ph = 218
    pw = 322
    for i, f in enumerate(FEATURES):
        fx = x0 + i * (pw + 11)
        cv.outline_rect(fx, y, pw, ph, INK, 1)
        cv.set_clip(fx + 1, y + 1, pw - 2, 84)
        SCENES[f["scene"]](cv, (fx + 1, y + 1, pw - 2, 84))
        cv.reset_clip()
        cv.fill_rect(fx + 1, y + 84, pw - 2, 18, RED)
        draw_text(cv, fx + 8, y + 87, f["kicker"], 13, (255, 255, 255), bold=True)
        draw_text(cv, fx + 8, y + 106, f["loc"], 11, RED, bold=True)
        head_lines = wrap(f["head"], 19, True, pw - 16, max_lines=2)
        draw_lines(cv, fx + 8, y + 120, head_lines, 19, INK, bold=True, lh=21)
        body_lines = wrap(f["body"], 11, False, pw - 16, max_lines=3)
        draw_lines(cv, fx + 8, y + 164, body_lines, 11, INK, lh=13)
        draw_text(cv, fx + 8, y + 206, f["src"], 9, MUTED)

    # mediums: 2 rows x 5
    my = 452
    mw, mh = 190, 122
    xs = [18, 217, 417, 616, 816]
    for row in range(2):
        for col in range(5):
            m = MEDIUMS[row * 5 + col]
            mx = xs[col]
            yy = my + row * (mh + 6)
            cv.outline_rect(mx, yy, mw, mh, INK, 1)
            cv.set_clip(mx + 1, yy + 1, mw - 2, 40)
            SCENES[m["scene"]](cv, (mx + 1, yy + 1, mw - 2, 40))
            cv.reset_clip()
            cv.fill_rect(mx + 1, yy + 40, mw - 2, 15, RED)
            draw_text(cv, mx + 6, yy + 42, m["kicker"], 11, (255, 255, 255), bold=True)
            head_lines = wrap(m["head"], 14, True, mw - 12, max_lines=2)
            draw_lines(cv, mx + 6, yy + 58, head_lines, 14, INK, bold=True, lh=16)
            body_lines = wrap(m["body"], 10, False, mw - 12, max_lines=2)
            draw_lines(cv, mx + 6, yy + 90, body_lines, 10, INK, lh=11)
            draw_text(cv, mx + 6, yy + 112, m["src"], 9, MUTED)

    # map + also list
    y = 710
    mh2 = 186
    # map panel
    cv.outline_rect(x0, y, 480, mh2, INK, 1)
    draw_text(cv, x0 + 8, y + 4, "WHERE IT HAPPENED · numbered as the stories", 12, INK, bold=True)
    draw_map(cv, x0 + 8, y + 22, 464, 138)
    # legend: dot + label, measured widths, two rows
    lx, ly = x0 + 8, y + 163
    for i, (name, count) in enumerate(REGIONS):
        row = i // 4
        if i % 4 == 0 and i:
            lx = x0 + 8
            ly = y + 175
        label = "%s %d" % (name, count)
        cv.circle(lx + 3, ly + 4, 3, REGION_COLORS[name])
        draw_text(cv, lx + 9, ly, label, 10, INK)
        lx += 9 + text_width(label, 10, False) + 16
    # also panel
    ax = 506
    aw = 500
    cv.outline_rect(ax, y, aw, mh2, INK, 1)
    cv.fill_rect(ax + 1, y + 1, aw - 2, 20, INK)
    draw_text(cv, ax + 8, y + 4, "ALSO ON WEDNESDAY 25 NOVEMBER — 22 MORE STORIES",
              13, (255, 255, 255), bold=True)
    colw = (aw - 16) // 2
    for i, (num, txt) in enumerate(ALSO):
        col = i // 11
        row = i % 11
        ix = ax + 8 + col * colw
        iy = y + 26 + row * 14
        draw_text(cv, ix, iy, "%d ·" % num, 10, RED, bold=True)
        draw_text(cv, ix + 24, iy, txt, 10, INK)

    # date check
    y = 904
    cv.outline_rect(x0, y, cw, 70, RED, 2)
    draw_text(cv, x0 + 10, y + 6, "DATE CHECK", 13, RED, bold=True)
    dc_lines = wrap(DATE_CHECK, 11, False, cw - 20, max_lines=4)
    draw_lines(cv, x0 + 10, y + 24, dc_lines, 11, INK, lh=13)

    # footer
    y = 982
    cv.hline(x0, y, cw, INK, 2)
    draw_text(cv, x0, y + 8,
              "Every story here happened, or was first reported, on Wednesday 25 November 2026 in at least one time zone.",
              11, INK)
    draw_text(cv, x1, y + 8, "Sources named beside each story · Original drawings.",
              11, MUTED, align="right")
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    if not os.path.isdir(outdir):
        outdir = "out"
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    path = os.path.join(outdir, "entry.png")
    write_png(path, cv.buf, W, H)
    print("wrote %s (%d bytes)" % (path, os.path.getsize(path)))


if __name__ == "__main__":
    main()
