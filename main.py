#!/usr/bin/env python3
"""World news in one image -- Monday 23 November 2026 (round 2).

Draws a 1024x1024 newspaper front page summarising five verified
stories of 23 November 2026 and writes it to /output/entry.png.

Stdlib only: struct, sys, zlib, hashlib. No network access, no eval,
no dynamic imports, no environment access, no shell. The program reads
nothing from the environment and runs nothing but its own code, so the
output is byte-identical on every run (fixed zlib level, no timestamps
in the PNG).

Stories (all verified against Reuters/AP/UN News, see riset-2.md):
  1. Dymer toll rises to 11 (Monday morning, Kyiv region mourns)
  2. Ukraine sinks Russian corvette Merkury off Libya (Zelenskyy says)
  3. Democrats win 258 US House seats (biggest since 1992)
  4. After COP31 collapses, blame begins (Monday reactions)
  5. Drones hit Khartoum (Sunday strikes, UN/US condemn Monday)

Claims are kept separate from facts in the labels: "Zelenskyy says",
"Sudan alleges". Dates use neutral phrases ("Sunday", "Monday",
"announced Monday") and the masthead date stays MONDAY, 23 NOVEMBER
2026, the day being summarised.
"""

import hashlib
import struct
import sys
import zlib

# ---------------------------------------------------------------- font
# 5x7 bitmap font. Each glyph is 7 rows of 5 cells; '#' is ink.
# Only the characters used by the page text are defined; rendering
# uppercases everything first, so no lowercase glyphs are needed.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "*": (".....", ".#.#.", ".###.", "#####", ".###.", ".#.#.", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
}

# ---------------------------------------------------------------- canvas
W = 1024
H = 1024

PAPER = (250, 246, 235)   # warm newsprint
CARD = (255, 255, 255)    # panel fill
INK = (18, 18, 18)        # headlines, borders
BODY = (38, 38, 38)       # body text
MUTED = (110, 105, 95)    # footer text
NAVY = (16, 32, 66)       # masthead
RED = (178, 24, 28)       # date ribbon, hero accent
BLUE = (28, 68, 142)      # Merkury panel accent
STEEL = (24, 84, 130)     # Democrats panel accent
GREEN = (22, 110, 70)     # COP31 panel accent
PURPLE = (110, 40, 140)   # Khartoum panel accent

canvas = bytearray(W * H * 3)
for _i in range(W * H):
    canvas[_i * 3] = PAPER[0]
    canvas[_i * 3 + 1] = PAPER[1]
    canvas[_i * 3 + 2] = PAPER[2]


def rect(x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = yy * W * 3
        for xx in range(x0, x1):
            o = base + xx * 3
            canvas[o] = color[0]
            canvas[o + 1] = color[1]
            canvas[o + 2] = color[2]


def border(x, y, w, h, color, t=2):
    rect(x, y, w, t, color)
    rect(x, y + h - t, w, t, color)
    rect(x, y, t, h, color)
    rect(x + w - t, y, t, h, color)


def text_width(text, scale):
    """Pixel width of text at the given scale (no trailing advance)."""
    return len(text) * 6 * scale - scale


def draw_text(x, y, text, scale, color):
    text = text.upper()
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            raise ValueError("missing glyph for %r" % ch)
        for row in range(7):
            grow = glyph[row]
            for col in range(5):
                if grow[col] == "#":
                    rect(cx + col * scale, y + row * scale,
                         scale, scale, color)
        cx += 6 * scale


def wrap(text, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    words = text.upper().split(" ")
    lines = []
    cur = ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur = cur + " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for line in lines:
        if len(line) > max_chars:
            raise ValueError("unwrappable line %r" % line)
    return lines

# ---------------------------------------------------------------- layout
MARGIN = 24
CONTENT_W = W - 2 * MARGIN  # 976


def draw_centered(y, text, scale, color):
    x = (W - text_width(text, scale)) // 2
    draw_text(x, y, text, scale, color)


def draw_panel(x, y, w, h, accent, kicker, headline, body,
               head_scale=4, body_scale=3, max_body_lines=5):
    """One story card: white fill, ink border, accent top bar."""
    rect(x, y, w, h, CARD)
    border(x, y, w, h, INK, 2)
    rect(x + 2, y + 2, w - 4, 6, accent)
    ix = x + 18
    iw = w - 36
    # kicker (scale 2)
    if text_width(kicker, 2) > iw:
        raise ValueError("kicker too wide: %r" % kicker)
    draw_text(ix, y + 16, kicker, 2, accent)
    # headline (wrapped, scale head_scale)
    head_chars = iw // (6 * head_scale)
    head_lines = wrap(headline, head_chars)
    for i, line in enumerate(head_lines):
        if text_width(line, head_scale) > iw:
            raise ValueError("headline line too wide: %r" % line)
        draw_text(ix, y + 42 + i * (7 * head_scale + 4), line,
                  head_scale, INK)
    # body (wrapped, scale body_scale)
    body_chars = iw // (6 * body_scale)
    body_lines = wrap(body, body_chars)
    if len(body_lines) > max_body_lines:
        raise ValueError("body overflows: %d lines: %r"
                         % (len(body_lines), body))
    by = y + 42 + len(head_lines) * (7 * head_scale + 4) + 10
    for i, line in enumerate(body_lines):
        draw_text(ix, by + i * (7 * body_scale + 5), line,
                  body_scale, BODY)
    print("panel %-28r head=%d body=%d"
          % (kicker, len(head_lines), len(body_lines)))


def draw_page():
    # Masthead
    rect(MARGIN, 24, CONTENT_W, 84, NAVY)
    draw_centered(24 + 10, "WORLD NEWS", 9, (255, 255, 255))
    # Date ribbon
    rect(MARGIN, 116, CONTENT_W, 56, RED)
    draw_centered(116 + 14, "MONDAY, 23 NOVEMBER 2026", 4,
                  (255, 255, 255))

    # Hero: Dymer toll rises to 11 (Monday update of round-1 story 3)
    hx, hy, hw, hh = MARGIN, 182, CONTENT_W, 252
    rect(hx, hy, hw, hh, CARD)
    border(hx, hy, hw, hh, INK, 2)
    rect(hx + 2, hy + 2, hw - 4, 6, RED)
    hero_kicker = "UKRAINE - DYMER, NEAR KYIV - MONDAY TOLL RISES"
    hero_head = "DYMER TOLL RISES TO 11"
    hero_body = ("RESCUERS PULL AN 11TH BODY FROM THE DYMER FLATS MONDAY. "
                 "A 7-YEAR-OLD BOY IS PULLED OUT ALIVE. KYIV REGION "
                 "MOURNS AS THE WEEKEND TOLL HITS 15.")
    if text_width(hero_kicker, 2) > hw - 40:
        raise ValueError("hero kicker too wide")
    draw_text(hx + 20, hy + 16, hero_kicker, 2, RED)
    if text_width(hero_head, 7) > hw - 40:
        raise ValueError("hero headline too wide")
    draw_text(hx + 20, hy + 42, hero_head, 7, INK)
    hero_lines = wrap(hero_body, (hw - 40) // (6 * 4))
    if len(hero_lines) > 4:
        raise ValueError("hero body overflows: %d lines" % len(hero_lines))
    for i, line in enumerate(hero_lines):
        draw_text(hx + 20, hy + 105 + i * 34, line, 4, BODY)
    print("hero head=1 body=%d" % len(hero_lines))

    # Grid 2x2
    gw = (CONTENT_W - 12) // 2  # 482
    panels = [
        (MARGIN, 446, BLUE,
         "UKRAINE - BENGHAZI, LIBYA - MONDAY",
         "UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA",
         "ZELENSKYY SAYS 7 SEA DRONES SANK THE CORVETTE MERKURY "
         "SUNDAY. ANGARA ALSO HIT."),
        (MARGIN + gw + 12, 446, STEEL,
         "USA - WASHINGTON - SUNDAY",
         "DEMOCRATS WIN 258 HOUSE SEATS",
         "BIGGEST US HOUSE MAJORITY SINCE 1992. A NORTH CAROLINA "
         "RECOUNT WIN SEALS A 44-SEAT SWEEP."),
        (MARGIN, 710, GREEN,
         "CLIMATE - AFTER COP31 - MONDAY",
         "COP31 FALLOUT: BLAME BEGINS",
         "AUSTRALIA'S OPPOSITION WANTS THE MINISTER OUT. PACIFIC "
         "ISLANDS SAY 'LET DOWN'. NEXT: ADDIS ABABA 2027."),
        (MARGIN + gw + 12, 710, PURPLE,
         "SUDAN - KHARTOUM - SUNDAY",
         "DRONES HIT KHARTOUM",
         "SUNDAY STRIKES KILL CHILDREN AND WOUND 3 UN STAFF. UN AND "
         "US CONDEMN MONDAY. SUDAN ALLEGES AN ETHIOPIAN LAUNCH."),
    ]
    for (px, py, accent, kicker, headline, body) in panels:
        draw_panel(px, py, gw, 252, accent, kicker, headline, body)

    # Footer
    draw_centered(978,
                  "FIVE STORIES FROM AROUND THE WORLD - "
                  "SOURCES: REUTERS, AP, UN NEWS",
                  2, MUTED)


# ---------------------------------------------------------------- png
def png_bytes():
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += canvas[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    draw_page()
    data = png_bytes()
    if len(data) > 1048576:
        raise SystemExit("entry.png over 1 MiB: %d bytes" % len(data))
    path = sys.argv[1] if len(sys.argv) > 1 else "/output/entry.png"
    try:
        with open(path, "wb") as f:
            f.write(data)
    except OSError:
        path = "entry.png"
        with open(path, "wb") as f:
            f.write(data)
    print("wrote %s %d bytes sha256=%s"
          % (path, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
