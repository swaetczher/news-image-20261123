#!/usr/bin/env python3
"""World news front page for Monday 23 November 2026.

Writes one image to /output/entry.png (or $OUTPUT_PATH).
Stdlib only, no network, deterministic: two runs write identical bytes.

Layout: newspaper front page. Masthead, big date band, one hero story
(COP31 collapse) plus four stories in a 2x2 grid. A second layout
(poster: tall hero left, stacked panels right) is selectable with
LAYOUT=b for pairwise comparison; the default is the newspaper layout.
"""

import os
import struct
import zlib

# Pairwise verdict, 23 Nov 2026 (checked from the rendered PNGs, full size
# and downscaled to 300 px wide): layout A wins over layout B. In A every
# story body is scale 3, so all five headlines and bodies stay legible at
# 300 px; in B the two right-column stories drop to scale 2 bodies that turn
# to grey mush at 300 px, and the tall hero wastes its lower third on empty
# paper. A is also the cleaner newspaper composition: one hero, one even
# 2x2 grid, no dead space. Default stays "a"; B is kept only as a comparison
# reference selectable with LAYOUT=b.

W = 1024
H = 1024

PAPER = (247, 243, 234)
INK = (26, 26, 26)
NAVY = (20, 33, 61)
RED = (185, 28, 28)
GOLD = (217, 119, 6)
WHITE = (255, 255, 255)
LIGHT = (238, 234, 224)
GREEN = (22, 101, 52)
BLUE = (29, 78, 216)
TEAL = (15, 118, 110)
PURPLE = (126, 34, 206)
GREY = (90, 88, 82)

# ---------------------------------------------------------------------------
# 5x7 bitmap font, drawn from scratch. Each glyph is 7 rows of 5 bits.
# ---------------------------------------------------------------------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01101", "10011", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "10110", "11001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01101", "10011", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11110", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "#": ("01010", "01010", "11111", "01010", "01010", "11111", "01010"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
}


# ---------------------------------------------------------------------------
# Canvas helpers
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill(x0, y0, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, rad, color, thick=2):
        # Midpoint circle outline.
        x = rad
        y = 0
        err = 0
        while x >= y:
            for px, py in ((cx + x, cy + y), (cx + y, cy + x),
                           (cx - y, cy + x), (cx - x, cy + y),
                           (cx - x, cy - y), (cx - y, cy - x),
                           (cx + y, cy - x), (cx + x, cy - y)):
                self.fill(px, py, thick, thick, color)
            y += 1
            err += 1 + 2 * y
            if 2 * (err - x) + 1 > 0:
                x -= 1
                err += 1 - 2 * x


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, color, align="left"):
    if align == "center":
        x = x - text_width(text, scale) // 2
    elif align == "right":
        x = x - text_width(text, scale)
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            glyph = FONT[" "]
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.fill(cx + col * scale, y + row * scale,
                            scale, scale, color)
        cx += 6 * scale


def wrap(text, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# Story data (verified 23 Nov 2026 morning, WIB)
# ---------------------------------------------------------------------------
HERO = {
    "kicker": "CLIMATE SUMMIT - ANTALYA - SUNDAY",
    "kicker_short": "CLIMATE - ANTALYA - SUNDAY",
    "headline": ["COP31 COLLAPSES:", "NO CLIMATE DEAL"],
    "body": ("EU, UK and vulnerable nations reject a draft that never "
             "mentions fossil fuels. The longest climate summit in history "
             "ends with no pact."),
    "accent": GREEN,
}

STORIES = [
    {
        "kicker": "THE GULF - BAHRAIN - SATURDAY NIGHT",
        "kicker_short": "GULF - BAHRAIN - SAT NIGHT",
        "headline": ["IRAN HITS US BASES", "IN BAHRAIN"],
        "headline_narrow": ["IRAN HITS", "US BASES IN", "BAHRAIN"],
        "body": ("Bahrain: 2 hurt, a plant on fire. Iran CLAIMS 2 Patriot "
                 "radars destroyed."),
        "accent": RED,
        "icon": "missile",
    },
    {
        "kicker": "UKRAINE - DYMER, NEAR KYIV - SUNDAY",
        "kicker_short": "UKRAINE - DYMER - SUNDAY",
        "headline": ["DRONE COLLAPSES", "FLATS NEAR KYIV"],
        "headline_narrow": ["DRONE", "COLLAPSES", "FLATS NEAR KYIV"],
        "body": ("At least 2 dead, 11-15 missing. A Russian drone brings "
                 "down a 5-storey block."),
        "accent": BLUE,
        "icon": "building",
    },
    {
        "kicker": "TRADE - BRUSSELS - SATURDAY",
        "headline": ["EU-INDONESIA SIGN", "MEGA TRADE DEAL"],
        "body": ("After a decade of talks, CEPA is signed. Tariffs gone on "
                 "98.5% of lines. Not yet in force."),
        "accent": TEAL,
        "icon": "arrows",
    },
    {
        "kicker": "HONG KONG - SUNDAY",
        "headline": ["HONG KONG VOTES:", "98.79% TURNOUT"],
        "body": ("856 candidates, 723 seats: the Election Committee picks "
                 "the next leader in 2027."),
        "accent": PURPLE,
        "icon": "ballot",
    },
]


# ---------------------------------------------------------------------------
# Small pictogram icons, drawn with lines and rectangles
# ---------------------------------------------------------------------------
def draw_icon(cv, kind, x, y, size, color):
    if kind == "globe":
        cx, cy = x + size // 2, y + size // 2
        r = size // 2 - 4
        cv.circle(cx, cy, r, color, 4)
        cv.line(cx - r, cy, cx + r, cy, color, 3)
        cv.line(cx, cy - r, cx, cy + r, color, 3)
        cv.line(cx - r + 8, cy - r + 10, cx + r - 8, cy - r + 10, color, 3)
        cv.line(cx - r + 8, cy + r - 10, cx + r - 8, cy + r - 10, color, 3)
    elif kind == "missile":
        cv.line(x + 8, y + size - 8, x + size - 14, y + 14, color, 6)
        cv.fill(x + size - 22, y + 4, 18, 18, color)
        cv.fill(x + 2, y + size - 26, 16, 6, color)
        cv.fill(x + 14, y + size - 14, 6, 16, color)
        cv.fill(x + 2, y + size - 8, 8, 8, GOLD)
    elif kind == "building":
        cv.fill(x + 4, y + size // 3, size // 3, size * 2 // 3 - 4, color)
        cv.fill(x + size // 2, y + 8, size // 3, size - 12, color)
        cv.line(x + 4, y + size // 3 - 8, x + size // 2, y + size // 3 - 8,
                color, 4)
        for wy in (y + size // 2, y + size * 2 // 3, y + size * 5 // 6):
            cv.fill(x + 10, wy, 6, 6, WHITE)
            cv.fill(x + size // 2 + 8, wy - 8, 6, 6, WHITE)
    elif kind == "arrows":
        cv.line(x + 6, y + size // 3, x + size - 16, y + size // 3, color, 5)
        cv.line(x + size - 16, y + size // 3, x + size - 26, y + size // 3 - 10,
                color, 5)
        cv.line(x + size - 16, y + size // 3, x + size - 26, y + size // 3 + 10,
                color, 5)
        cv.line(x + size - 6, y + size * 2 // 3, x + 16, y + size * 2 // 3,
                color, 5)
        cv.line(x + 16, y + size * 2 // 3, x + 26, y + size * 2 // 3 - 10,
                color, 5)
        cv.line(x + 16, y + size * 2 // 3, x + 26, y + size * 2 // 3 + 10,
                color, 5)
    elif kind == "ballot":
        cv.fill(x + 6, y + size // 3, size - 12, size * 2 // 3 - 6, color)
        cv.fill(x + size // 4, y + size // 3 + 6, size // 2, 6, WHITE)
        cv.line(x + 10, y + size // 2 + 10, x + size // 2 - 4, y + size - 12,
                WHITE, 5)
        cv.line(x + size // 2 - 4, y + size - 12, x + size - 12, y + 8,
                WHITE, 5)


# ---------------------------------------------------------------------------
# Panels
# ---------------------------------------------------------------------------
def draw_panel(cv, x, y, w, h, story, head_scale=4, body_scale=3):
    cv.fill(x, y, w, h, WHITE)
    cv.fill(x, y, w, 8, story["accent"])
    # thin border
    cv.fill(x, y, w, 2, INK)
    cv.fill(x, y + h - 2, w, 2, INK)
    cv.fill(x, y, 2, h, INK)
    cv.fill(x + w - 2, y, 2, h, INK)
    pad = 20
    inner = w - 2 * pad
    ty = y + 22
    draw_text(cv, x + pad, ty, story["kicker"], 2, story["accent"])
    ty += 14 + 12
    for line in story["headline"]:
        draw_text(cv, x + pad, ty, line, head_scale, INK)
        ty += 7 * head_scale + 6
    ty += 4
    for line in wrap(story["body"], body_scale, inner):
        draw_text(cv, x + pad, ty, line, body_scale, INK)
        ty += 7 * body_scale + 4


def draw_masthead(cv):
    cv.fill(24, 24, 976, 96, NAVY)
    draw_text(cv, 512, 44, "WORLD NEWS", 10, WHITE, align="center")
    cv.fill(24, 128, 976, 58, RED)
    draw_text(cv, 512, 143, "MONDAY, 23 NOVEMBER 2026", 5, WHITE,
              align="center")


def draw_footer(cv):
    draw_text(cv, 512, 1002,
              "FIVE STORIES FROM AROUND THE WORLD - SOURCES: UN NEWS, REUTERS, AP",
              2, GREY, align="center")


# ---------------------------------------------------------------------------
# Layout A — newspaper: hero full width, then a 2x2 grid
# ---------------------------------------------------------------------------
def layout_a(cv):
    draw_masthead(cv)
    # hero
    hx, hy, hw, hh = 24, 194, 976, 288
    cv.fill(hx, hy, hw, hh, WHITE)
    cv.fill(hx, hy, hw, 10, GREEN)
    cv.fill(hx, hy, hw, 2, INK)
    cv.fill(hx, hy + hh - 2, hw, 2, INK)
    cv.fill(hx, hy, 2, hh, INK)
    cv.fill(hx + hw - 2, hy, 2, hh, INK)
    draw_text(cv, hx + 24, hy + 28, HERO["kicker"], 3, GREEN)
    ty = hy + 28 + 21 + 14
    for line in HERO["headline"]:
        draw_text(cv, hx + 24, ty, line, 7, INK)
        ty += 7 * 7 + 8
    ty += 6
    for line in wrap(HERO["body"], 3, hw - 48):
        draw_text(cv, hx + 24, ty, line, 3, INK)
        ty += 7 * 3 + 5
    # 2x2 grid
    gx, gy = 24, 496
    pw, ph = 480, 240
    gap = 16
    for i, story in enumerate(STORIES):
        px = gx + (i % 2) * (pw + gap)
        py = gy + (i // 2) * (ph + gap)
        draw_panel(cv, px, py, pw, ph, story)
    draw_footer(cv)


# ---------------------------------------------------------------------------
# Layout B — poster: tall hero left, stacked panels right, bottom row
# ---------------------------------------------------------------------------
def layout_b(cv):
    draw_masthead(cv)
    # tall hero on the left
    hx, hy, hw, hh = 24, 194, 592, 506
    cv.fill(hx, hy, hw, hh, WHITE)
    cv.fill(hx, hy, hw, 10, GREEN)
    cv.fill(hx, hy, hw, 2, INK)
    cv.fill(hx, hy + hh - 2, hw, 2, INK)
    cv.fill(hx, hy, 2, hh, INK)
    cv.fill(hx + hw - 2, hy, 2, hh, INK)
    draw_text(cv, hx + 24, hy + 28, HERO["kicker_short"], 3, GREEN)
    ty = hy + 28 + 21 + 16
    for line in ["COP31", "COLLAPSES:", "NO DEAL"]:
        draw_text(cv, hx + 24, ty, line, 8, INK)
        ty += 7 * 8 + 8
    ty += 8
    for line in wrap(HERO["body"], 3, 380):
        draw_text(cv, hx + 24, ty, line, 3, INK)
        ty += 7 * 3 + 5
    draw_icon(cv, "globe", hx + hw - 150, hy + hh - 150, 120, GREEN)
    # right column: two stacked panels (narrow kickers and headlines,
    # smaller body text so the copy fits the narrow column)
    rx, rw = 632, 368
    rh = 245
    for i in (0, 1):
        story = dict(STORIES[i])
        story["kicker"] = story["kicker_short"]
        story["headline"] = story["headline_narrow"]
        draw_panel(cv, rx, 194 + i * (rh + 16), rw, rh, story,
                   head_scale=3, body_scale=2)
    # bottom row: two panels
    bx, by, bw, bh = 24, 716, 480, 260
    for i in (2, 3):
        draw_panel(cv, bx + (i - 2) * (bw + 16), by, bw, bh, STORIES[i],
                   head_scale=4, body_scale=3)
    draw_footer(cv)


# ---------------------------------------------------------------------------
# Pure-Python PNG encoder (zlib from the stdlib)
# ---------------------------------------------------------------------------
def png_bytes(cv):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    layout = os.environ.get("LAYOUT", "a")
    out_path = os.environ.get("OUTPUT_PATH", "/output/entry.png")
    cv = Canvas(W, H, PAPER)
    if layout == "b":
        layout_b(cv)
    else:
        layout_a(cv)
    data = png_bytes(cv)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(data)
    print("wrote %s (%d bytes, %dx%d) sha256=%s"
          % (out_path, len(data), W, H,
             __import__("hashlib").sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
