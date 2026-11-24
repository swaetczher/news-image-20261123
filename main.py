# SPDX-License-Identifier: MIT
#!/usr/bin/env python3
"""news-image 20261123 -- ronde 4 (FINAL).

Satu gambar koran 1024x1024, stdlib-only, deterministik.
Resep: monocle-magazine (kertas krem, tinta, satu aksen merah editorial,
hairline, hierarki 3-deck kicker -> headline -> dek, radius 0).
Komposisi Mode C: editorial-cover (masthead + hero) + banner-grid-2x2.
Skema: TEMPLATE dict + DATA dict, anchor-based + relative positioning.

Pakai: python3 main.py [A|B|C] [output.png]
  varian A = classic (default), B = bold hero, C = airy.
  Tanpa argumen: varian A ke ./entry.png
Hanya import stdlib: hashlib, struct, sys, zlib. Tanpa network, tanpa
font/aset eksternal, tanpa angka acak, tanpa stempel waktu -> sha256
identik di setiap run.
"""

import hashlib
import struct
import sys
import zlib

W = 1024
H = 1024

# --- Design Decisions (monocle-magazine, dideklarasi sebelum kode) ---
# Palet (4 warna saja, sesuai resep; olive resep TIDAK dipakai):
PAPER = (0xF2, 0xEF, 0xE7)     # kertas krem #F2EFE7
INK = (0x1A, 0x1A, 0x1A)       # tinta #1A1A1A
ACCENT = (0xC7, 0x32, 0x2E)    # merah editorial #C7322E (tunggal)
HAIRLINE = (0xC8, 0xC2, 0xB0)  # hairline #C8C2B0
# Tipografi (font bitmap 5x7, 1 keluarga): masthead 6x, hero headline 5x,
# grid headline 3x, body 2x, kicker 2x, footer 1x.
# Rasio hero headline / body = 5/2 = 2,5x (batas resep). Radius 0.
# Spacing: unit dasar 8 px; margin 32; gutter grid 24 (A) / 16 (B) / 32 (C).

MX = 32            # margin kiri/kanan
CW = W - 2 * MX    # lebar konten = 960

# --- Font bitmap 5x7 (ditulis dari nol; '#' = piksel tinta) ---
# Tiap glyph: 7 baris x 5 kolom. Hanya huruf besar + angka + tanda baca
# yang dipakai DATA; teks kecil otomatis diubah ke huruf besar.
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
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
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
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "&": (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.#..", "#....", ".###."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
}

for _g in FONT.values():
    assert len(_g) == 7 and all(len(_r) == 5 for _r in _g)


def text_w(text, scale):
    """Lebar piksel teks pada skala tertentu (1 kolom spasi antar huruf)."""
    return len(text) * 6 * scale - scale


def wrap(text, max_chars):
    """Bungkus kata per kata; satu kata yang lebih panjang dari batas = error."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        if len(word) > max_chars:
            raise ValueError("kata terlalu panjang untuk lebar panel: " + word)
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --- Kanvas ---
class Canvas:
    def __init__(self):
        self.px = bytearray(PAPER * (W * H))

    def _put(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self._put(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def char(self, x, y, ch, scale, color):
        glyph = FONT.get(ch)
        if glyph is None:
            raise ValueError("glyph tidak ada di font: " + repr(ch))
        for r in range(7):
            row = glyph[r]
            for c in range(5):
                if row[c] == "#":
                    self.rect(x + c * scale, y + r * scale, scale, scale, color)

    def text(self, x, y, s, scale, color):
        s = s.upper()
        if x < 0 or y < 0 or y + 7 * scale > H:
            raise ValueError("teks keluar kanvas: " + s[:20])
        cx = x
        for ch in s:
            self.char(cx, y, ch, scale, color)
            cx += 6 * scale
        if cx - scale > W:
            raise ValueError("teks keluar kanvas: " + s[:20])
        return cx

    def text_center(self, x0, width, y, s, scale, color):
        wpx = text_w(s.upper(), scale)
        return self.text(x0 + (width - wpx) // 2, y, s, scale, color)


# --- Relative positioning (snapping ala Canva) ---
def below(y_bottom, gap):
    return y_bottom + gap


def right_of(x_right, gap):
    return x_right + gap


def center_in(x0, width, text, scale):
    return x0 + (width - text_w(text.upper(), scale)) // 2


# --- Skema template poster-generator-layout (satu sumber kebenaran) ---
# TEMPLATE: settings + anchors + layers (background -> content -> foreground)
# + grup headers / hero / grid / footer. DATA: isi edisi.
TEMPLATE = {
    "schema": "1.0",
    "settings": {"width": 1024, "height": 1024, "background_color": "#F2EFE7"},
    "anchors": {
        "masthead_bottom": {"x": 0, "y": 66},
        "hero_top": {"x": 32, "y": 136},
        "grid_top": {"x": 32, "y": 336},
        "footer_top": {"x": 32, "y": 962},
    },
    "layers": ["background", "content", "foreground"],
    "groups": ["headers", "hero", "grid", "footer"],
}

# DATA edisi (5 berita riset-4 + tanggal). Label klaim WAJIB:
# 1 "under investigation" | 2 "coalition says" | 3 "around 175" +
# "left Dakar about two weeks ago" | 5 "states allege" + "filed Monday".
DATA = {
    "masthead_text": "THE WORLD IN ONE DAY",
    "dateline": "WEDNESDAY, 25 NOVEMBER 2026",
    "dateline_right": "FIVE STORIES - ONE PAGE",
    "hero_kicker": "01 - CHINA - ANNOUNCED TUESDAY",
    "hero_title": "CHINA PROBES POLITBURO MEMBER",
    "hero_dek": (
        "Shanghai party chief Chen Jining under investigation for suspected "
        "severe violations of discipline and laws. The fourth Politburo "
        "member probed since 2025."
    ),
    "hero_fact": "AGE 62 - SHANGHAI PARTY CHIEF - FOURTH SINCE 2025",
    "stories": [
        {
            "num": "02",
            "kicker": "SAUDI ARABIA - COALITION SAYS",
            "title": "RIYADH TOWER TARGETED",
            "body": (
                "Coalition calls it a terrorist attack on Tuesday. Houthis "
                "struck the PIF tower and an Aramco building this month. "
                "No tower name, culprit or toll was given."
            ),
            "fact": "8 NOV - ARAMCO BUILDING HIT",
        },
        {
            "num": "03",
            "kicker": "SENEGAL - AROUND 175 MISSING",
            "title": "MIGRANT BOAT LOST OFF SENEGAL",
            "body": (
                "Europe-bound boat left Dakar about two weeks ago. Contact "
                "lost with around 175 people aboard. Senegal's navy rescued "
                "974 migrants on Monday."
            ),
            "fact": "5,200 RESCUED SINCE EARLY NOVEMBER",
        },
        {
            "num": "04",
            "kicker": "IRAQ - AFTER SMUGGLING PROBE",
            "title": "BAGHDAD SEIZES KURDISH CROSSINGS",
            "body": (
                "PM orders a federal takeover of border crossings and "
                "oilfields in four provinces on Tuesday. Oil funds over 90 "
                "percent of state revenue."
            ),
            "fact": "120,000 BARRELS A DAY",
        },
        {
            "num": "05",
            "kicker": "UNITED STATES - STATES ALLEGE",
            "title": "TWO STATES SUE SPACEX OVER GROK",
            "body": (
                "Virginia and Oregon filed suit Monday alleging the chatbot "
                "made sexual images, including child abuse material. The "
                "states seek damages and a court order."
            ),
            "fact": "2,500 DOLLARS PER WILFUL VIOLATION",
        },
    ],
    "footer_left": "SOURCES: REUTERS AND AP - CLAIMS LABELLED AS REPORTED",
    "footer_right": "PAGE 1 - 25 NOVEMBER 2026",
}

# Varian dari template + resep yang SAMA (beda hierarki/spacing saja).
PARAMS = {
    # A classic: masthead 6x, hero headline 5x satu baris, grid headline 3x.
    "A": {"masthead": 6, "hero_head": 5, "grid_head": 3, "gutter": 24,
          "hero_gap": 14, "grid_gap": 24},
    # B bold hero: masthead 5x, hero headline 6x dua baris, grid headline 2x.
    "B": {"masthead": 5, "hero_head": 6, "grid_head": 2, "gutter": 16,
          "hero_gap": 12, "grid_gap": 16},
    # C airy: masthead 6x, hero headline 5x, grid headline 3x, gutter lega.
    "C": {"masthead": 6, "hero_head": 5, "grid_head": 3, "gutter": 32,
          "hero_gap": 18, "grid_gap": 32},
}


def check_data():
    """Semua variabel terisi + semua karakter ada di font (bukan string kosong)."""
    for key, val in DATA.items():
        if isinstance(val, str):
            if not val.strip():
                raise ValueError("variabel kosong: " + key)
            for ch in val.upper():
                if ch not in FONT:
                    raise ValueError("karakter tak didukung: " + repr(ch))
    for st in DATA["stories"]:
        for key in ("num", "kicker", "title", "body", "fact"):
            if not st[key].strip():
                raise ValueError("variabel kosong: story " + key)
            for ch in st[key].upper():
                if ch not in FONT:
                    raise ValueError("karakter tak didukung: " + repr(ch))


# --- Render (layer: background -> content -> foreground) ---
def render(variant):
    if variant not in PARAMS:
        raise ValueError("varian tidak dikenal: " + variant + " (pilih A/B/C)")
    p = PARAMS[variant]
    check_data()
    cv = Canvas()
    anchors = {}

    # ===== LAYER background =====
    cv.rect(0, 0, W, H, PAPER)

    # ===== LAYER content =====
    # --- grup headers: masthead + dateline ---
    y = 24
    cv.text_center(MX, CW, y, DATA["masthead_text"], p["masthead"], INK)
    anchors["masthead_bottom"] = y + 7 * p["masthead"]
    y = below(anchors["masthead_bottom"], 12)
    cv.hline(MX, y, CW, ACCENT, 3)
    y = below(y + 3, 10)
    cv.text(MX, y, DATA["dateline"], 2, INK)
    rx = MX + CW - text_w(DATA["dateline_right"], 2)
    cv.text(rx, y, DATA["dateline_right"], 2, ACCENT)
    y = below(y + 14, 10)
    cv.hline(MX, y, CW, HAIRLINE, 1)

    # --- grup hero: kicker -> headline -> dek -> fact strip ---
    y = below(y + 1, 16)
    anchors["hero_top"] = y
    cv.text(MX, y, DATA["hero_kicker"], 2, ACCENT)
    y = below(y + 14, p["hero_gap"])
    max_head = CW // (6 * p["hero_head"])
    head_lines = wrap(DATA["hero_title"], max_head)
    for ln in head_lines:
        cv.text(MX, y, ln, p["hero_head"], INK)
        y += 7 * p["hero_head"] + 6
    y = below(y - 6, 14)
    dek_lines = wrap(DATA["hero_dek"], CW // 12)
    for ln in dek_lines:
        cv.text(MX, y, ln, 2, INK)
        y += 18
    y = below(y, 12)
    cv.hline(MX, y, CW, HAIRLINE, 1)
    y = below(y + 1, 10)
    cv.text(MX, y, DATA["hero_fact"], 2, INK)
    y = below(y + 14, 10)
    cv.hline(MX, y, CW, HAIRLINE, 1)
    anchors["hero_bottom"] = y + 1

    # --- grup grid: 2x2, hairline antar-kolom dan antar-baris ---
    gutter = p["gutter"]
    grid_top = below(anchors["hero_bottom"], p["grid_gap"])
    anchors["grid_top"] = grid_top
    footer_rule_y = 958
    avail = footer_rule_y - grid_top - 8
    row_h = (avail - gutter) // 2
    panel_w = (CW - gutter) // 2
    grid_bottom = grid_top + 2 * row_h + gutter
    mid_x = MX + panel_w + gutter // 2
    cv.vline(mid_x, grid_top, grid_bottom - grid_top, HAIRLINE, 1)
    mid_y = grid_top + row_h + gutter // 2
    cv.hline(MX, mid_y, CW, HAIRLINE, 1)

    for idx, st in enumerate(DATA["stories"]):
        col = idx % 2
        row = idx // 2
        px = MX + col * (panel_w + gutter)
        py = grid_top + row * (row_h + gutter)
        # kicker: nomor + topik, aksen merah tunggal
        cv.text(px, py, st["num"] + " - " + st["kicker"], 2, ACCENT)
        hy = below(py + 14, 10)
        max_gh = panel_w // (6 * p["grid_head"])
        gh_lines = wrap(st["title"], max_gh)
        for ln in gh_lines:
            cv.text(px, hy, ln, p["grid_head"], INK)
            hy += 7 * p["grid_head"] + 4
        by = below(hy - 4, 12)
        body_lines = wrap(st["body"], panel_w // 12)
        for ln in body_lines:
            cv.text(px, by, ln, 2, INK)
            by += 18
        # fact strip di dasar panel (hairline + angka kunci)
        fy = py + row_h - 34
        cv.hline(px, fy, panel_w, HAIRLINE, 1)
        cv.text(px, below(fy + 1, 8), st["fact"], 2, INK)

    # ===== LAYER foreground =====
    # --- grup footer ---
    cv.hline(MX, footer_rule_y, CW, HAIRLINE, 1)
    fy = below(footer_rule_y + 1, 12)
    cv.text(MX, fy, DATA["footer_left"], 1, INK)
    rx = MX + CW - text_w(DATA["footer_right"], 1)
    cv.text(rx, fy, DATA["footer_right"], 1, INK)
    anchors["footer_top"] = footer_rule_y
    return cv, anchors


# --- Encoder PNG pure-Python (deterministik: filter 0, level 9) ---
def chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += cv.px[yy * W * 3:(yy + 1) * W * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main(argv):
    variant = argv[1] if len(argv) > 1 else "A"
    out = argv[2] if len(argv) > 2 else "entry.png"
    cv, anchors = render(variant)
    data = encode_png(cv)
    with open(out, "wb") as f:
        f.write(data)
    digest = hashlib.sha256(data).hexdigest()
    print("varian=" + variant + " file=" + out + " byte=" + str(len(data)))
    print("sha256=" + digest)
    print("anchors=" + str(anchors))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
