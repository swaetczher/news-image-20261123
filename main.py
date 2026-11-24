#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""news-image 20261123 round 3: one 1024x1024 PNG summing up Tuesday 24 Nov 2026.

Stdlib only (hashlib, struct, sys, zlib). No network, no file reads, no
environment access, no eval/dynamic import/shell: the program only runs its
own code and writes one PNG file. Deterministic by construction: fixed
zlib level, no timestamps in the PNG.

Usage: python3 main.py [output_path] [variant]
  output_path defaults to /output/entry.png (kit convention)
  variant "A" (default): newspaper, hero + 2x2 grid, hero stock chart
  variant "B": newspaper, hero + 4 horizontal strips
"""

import hashlib
import struct
import sys
import zlib

W = 1024
H = 1024

NAVY = (15, 42, 74)
RED = (178, 34, 34)
DARK = (28, 28, 28)
GRAY = (96, 96, 96)
GREEN = (30, 122, 52)
LIGHT = (238, 238, 238)
BORDER = (198, 198, 198)
WHITE = (255, 255, 255)
ORANGE = (198, 82, 28)
PURPLE = (92, 62, 140)
DARKRED = (140, 30, 30)

# 5x7 bitmap font. Each glyph is 7 rows of 5 cells ('#' = ink).
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00010", "00100", "00100", "00100"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "01100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
    '%': ("10001", "10010", "00010", "00100", "01000", "01001", "10001"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10010", "01000", "10101", "10010", "01101"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '*': ("00000", "01010", "00100", "11111", "00100", "01010", "00000"),
}


def glyph(ch):
    return FONT.get(ch, FONT[' '])


def char_w(scale):
    return 6 * scale


def text_w(text, scale):
    return len(text) * char_w(scale) - scale


def wrap(text, max_chars):
    """Greedy word wrap. Returns list of lines, each <= max_chars."""
    words = text.split(' ')
    lines = []
    cur = ''
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def rect(self, x, y, w, h, color):
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

    def text(self, s, x, y, scale, color):
        s = s.upper()
        cx = x
        for ch in s:
            rows = glyph(ch)
            for ry in range(7):
                row = rows[ry]
                for rx in range(5):
                    if row[rx] == '1':
                        self.rect(cx + rx * scale, y + ry * scale,
                                  scale, scale, color)
            cx += char_w(scale)

    def text_centered(self, s, cx, y, scale, color):
        self.text(s, cx - text_w(s, scale) // 2, y, scale, color)


def png_bytes(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack('>IIBBBBB', canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', comp) + chunk(b'IEND', b''))

# ---- Content: Tuesday 24 November 2026 (all anchored Monday 23 Nov) ----
DATE_LINE = "TUESDAY, 24 NOVEMBER 2026"
FOOTER = "FIVE STORIES FROM AROUND THE WORLD - SOURCES: REUTERS, AP, CNN"

HERO = {
    "kicker": "BUSINESS - NVIDIA - MONDAY",
    "head": "HUANG IS BACK",
    "body": ("NVIDIA REINSTATES JENSEN HUANG AS CEO MONDAY AFTER TRUMP "
             "INTERVENES. SHARES SURGE 33%, NASDAQ JUMPS 6%."),
}

# Grid panels (variant A): kicker 1 line, head <= 3 lines @ scale 4,
# body <= 5 lines @ scale 3 (24 chars/line).
PANELS = [
    {
        "kicker": "INDONESIA - BANTEN",
        "head": "24 DEAD IN INDONESIA FACTORY FIRE",
        "body": ("SATURDAY BLAZE AT CIKANDE CANDY PLANT CONFIRMED MONDAY. "
                 "ABOUT 30 STILL MISSING. RESCUERS SEARCH RUINS."),
        "accent": ORANGE,
    },
    {
        "kicker": "SPACE - WESTERN INTELLIGENCE",
        "head": "NUCLEAR SATELLITE ALARM",
        "body": ("WESTERN INTEL SAYS RUSSIA COULD LAUNCH NUCLEAR-ARMED "
                 "'SPUTNIK-S' WITHIN WEEKS. NATO VOWS SPACE IS COVERED."),
        "accent": PURPLE,
    },
    {
        "kicker": "RUSSIA - KREMLIN",
        "head": "KREMLIN VOWS 'PAINFUL CONSEQUENCES'",
        "body": ("MOSCOW THREATENS KYIV MONDAY AFTER UKRAINE SAYS IT SANK "
                 "THE CORVETTE MERKURY OFF LIBYA. ROSTOV REFINERY HALTS."),
        "accent": DARKRED,
    },
    {
        "kicker": "USA - APPEALS COURT",
        "head": "COURT OPENS PATH TO ERASE TRUMP CONVICTION",
        "body": ("APPEALS PANEL REVIVES BID TO MOVE HUSH-MONEY CASE TO "
                 "FEDERAL COURT MONDAY. IMMUNITY FIGHT NEXT."),
        "accent": NAVY,
    },
]

# Strip headlines (variant B): head <= 2 lines @ scale 4 in 480 px.
STRIP_HEADS = [
    "24 DEAD IN INDONESIA FACTORY FIRE",
    "NUCLEAR SATELLITE ALARM",
    "KREMLIN VOWS 'PAINFUL CONSEQUENCES'",
    "COURT OPENS PATH TO ERASE CONVICTION",
]


# Strip bodies (variant B): <= 5 lines @ scale 3 in 412 px (22 chars/line).
STRIP_BODIES = [
    "SATURDAY BLAZE IN CIKANDE CONFIRMED MONDAY. ABOUT 30 STILL MISSING.",
    "WESTERN INTEL: RUSSIA COULD LAUNCH 'SPUTNIK-S' WITHIN WEEKS.",
    "MOSCOW THREATENS KYIV AFTER MERKURY SINKING. REFINERY HALTS.",
    "APPEALS PANEL REVIVES BID TO MOVE CASE TO FEDERAL COURT.",
]


def draw_masthead(cv):
    cv.rect(24, 24, 976, 84, NAVY)
    cv.text_centered("WORLD NEWS", 512, 40, 9, WHITE)
    cv.rect(24, 112, 976, 42, RED)
    cv.text_centered(DATE_LINE, 512, 121, 4, WHITE)


def draw_hero(cv, x, y, w, h, chart=True):
    cv.rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, 3, NAVY)
    cv.rect(x, y + h - 3, w, 3, NAVY)
    cv.rect(x, y, 3, h, NAVY)
    cv.rect(x + w - 3, y, 3, h, NAVY)
    tx = x + 24
    cv.text(HERO["kicker"], tx, y + 16, 2, RED)
    cv.text(HERO["head"], tx, y + 38, 7, NAVY)
    body_w = (w - 48 - 300) if chart else (w - 48)
    max_chars = body_w // char_w(4)
    lines = wrap(HERO["body"], max_chars)
    assert len(lines) <= 5, "hero body overflow: %r" % (lines,)
    yy = y + 104
    for line in lines:
        assert text_w(line, 4) <= body_w, "hero line too wide: %r" % line
        cv.text(line, tx, yy, 4, DARK)
        yy += 28
    if chart:
        # Rising-bars chart: Nvidia shares +33%.
        cx0 = x + w - 292
        base = y + h - 52
        cv.text("+33%", cx0 + 8, y + 96, 5, GREEN)
        cv.text("SHARES", cx0 + 8, y + 136, 2, GRAY)
        heights = [36, 62, 88, 116, 148]
        bx = cx0
        for i, hh in enumerate(heights):
            col = NAVY if i == 4 else GREEN
            cv.rect(bx, base - hh, 44, hh, col)
            bx += 54
        cv.rect(cx0, base, 264, 3, DARK)
        cv.text("NASDAQ +6%", cx0 + 8, base + 12, 2, GRAY)


def draw_panel(cv, p, x, y, w, h):
    cv.rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, 8, p["accent"])
    cv.rect(x, y, w, 2, BORDER)
    cv.rect(x, y + h - 2, w, 2, BORDER)
    cv.rect(x, y, 2, h, BORDER)
    cv.rect(x + w - 2, y, 2, h, BORDER)
    tx = x + 16
    inner = w - 32
    cv.text(p["kicker"], tx, y + 20, 2, RED)
    head_lines = wrap(p["head"], inner // char_w(4))
    assert len(head_lines) <= 3, "panel head overflow: %r" % (head_lines,)
    yy = y + 44
    for line in head_lines:
        assert text_w(line, 4) <= inner, "panel head too wide: %r" % line
        cv.text(line, tx, yy, 4, NAVY)
        yy += 28
    body_lines = wrap(p["body"], inner // char_w(3))
    assert len(body_lines) <= 5, "panel body overflow: %r" % (body_lines,)
    yy += 6
    for line in body_lines:
        assert text_w(line, 3) <= inner, "panel body too wide: %r" % line
        cv.text(line, tx, yy, 3, DARK)
        yy += 21


def draw_strip(cv, p, head, body, x, y, w, h):
    cv.rect(x, y, w, h, WHITE)
    cv.rect(x, y, 8, h, p["accent"])
    cv.rect(x, y, w, 2, BORDER)
    cv.rect(x, y + h - 2, w, 2, BORDER)
    cv.rect(x, y, 2, h, BORDER)
    cv.rect(x + w - 2, y, 2, h, BORDER)
    lx = x + 24
    cv.text(p["kicker"], lx, y + 14, 2, RED)
    head_lines = wrap(head, 520 // char_w(4))
    assert len(head_lines) <= 2, "strip head overflow: %r" % (head_lines,)
    yy = y + 36
    for line in head_lines:
        cv.text(line, lx, yy, 4, NAVY)
        yy += 28
    bx = x + 540
    body_lines = wrap(body, (w - 564) // char_w(3))
    assert len(body_lines) <= 5, "strip body overflow: %r" % (body_lines,)
    yy = y + 16
    for line in body_lines:
        cv.text(line, bx, yy, 3, DARK)
        yy += 21


def layout_a(cv):
    draw_masthead(cv)
    draw_hero(cv, 24, 162, 976, 286, chart=True)
    # 2x2 grid: panels 488x244, gap 16.
    xs = [24, 528]
    ys = [460, 716]
    for i, p in enumerate(PANELS):
        draw_panel(cv, p, xs[i % 2], ys[i // 2], 488, 244)
    cv.text_centered(FOOTER, 512, 976, 2, GRAY)


def layout_b(cv):
    draw_masthead(cv)
    draw_hero(cv, 24, 162, 976, 286, chart=True)
    # 4 horizontal strips, 976x118, gap 10.
    y = 460
    for i, p in enumerate(PANELS):
        draw_strip(cv, p, STRIP_HEADS[i], STRIP_BODIES[i], 24, y, 976, 118)
        y += 128
    cv.text_centered(FOOTER, 512, 976, 2, GRAY)


def main(argv):
    out = argv[1] if len(argv) > 1 else "/output/entry.png"
    variant = argv[2] if len(argv) > 2 else "A"
    cv = Canvas(W, H, WHITE)
    if variant == "B":
        layout_b(cv)
    else:
        layout_a(cv)
    data = png_bytes(cv)
    try:
        with open(out, "wb") as f:
            f.write(data)
    except OSError:
        with open("entry.png", "wb") as f:
            f.write(data)
        out = "entry.png"
    print("wrote %s variant=%s bytes=%d sha256=%s"
          % (out, variant, len(data), hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
