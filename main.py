#!/usr/bin/env python3
"""The World in One Day - Thursday 26 November 2026 (BATCH-B6-NEWSIMG26).

This program paints a one-page picture of the day's world news and
writes it as a PNG. The page is a broadsheet: a navy masthead, one wide
lead story across the top, six smaller stories in a two-by-three grid
underneath, and a light Thanksgiving line in the footer. Only the
Python standard library is used - the PNG writer, the small bitmap
alphabet and every pictogram are all defined in this file, so two runs
always produce the same bytes.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (1024 x 1024, deterministic).

The stories, gathered on the morning of 26 Nov 2026 from Reuters and
the day's wire summaries:

  LEAD  Trade - the Trump administration proposes new tariffs on 14
        major trading partners to fight excess factory capacity, with
        the highest rates aimed at China. It is the lead because it
        touches every trading bloc at once.
  1.    China - an anti-graft probe opens into Shanghai party chief
        Chen Jining, once tipped for the top table, upending the usual
        path to power ahead of next year's congress.
  2.    Space - a Pakistani astronaut becomes the first foreigner to
        board China's Tiangong space station, flying on Shenzhou-24.
  3.    Courts - a New York jury convicts Huawei of stealing US trade
        secrets in a sprawling trial over its Iran business.
  4.    Markets - Anthropic shares slide below their $83 IPO price
        days after a six-times-oversubscribed listing.
  5.    Gulf - Houthis claim an attack on a Saudi refinery and Brent
        crude tops $94 a barrel.
  6.    Colombia - police storm a supermarket and free 20 people held
        hostage for 17 hours.
  Footer - Thanksgiving Day in the US: Trump spares the turkeys
        Freedom and Feathers, the traditional light note.

Left out: the Bangladesh garment workers' 36 percent wage rise (real,
but regional), the Gukesh world chess title match (still mid-series),
and the Niger kidnapping of a Saudi national (still unconfirmed by
officials when this page was drawn).

Revision log:
  v1 - first render: lead panel plus a 2x3 grid, pictogram tile on the
       left of each small panel. PNG checked: valid header, 1024x1024,
       17,007 bytes.
  v2 - visual check of v1 found three faults: the letter D read as an
       arrowhead at small sizes (redrew its glyph with a straight
       spine), the lead panel's price-tag pictogram sat small in its
       tile (enlarged and centred), and the refinery-fire pictogram
       hid its stacks behind the flame (stacks moved out to the
       sides). Each small panel also gained a thin rule and a date
       line so the lower third no longer sits empty.
"""

import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024

# Palette: deep navy masthead on cream paper, brick-red accents.
CREAM = (250, 246, 233)
NAVY = (18, 32, 64)
INK = (26, 26, 30)
BRICK = (172, 44, 32)
GOLD = (176, 122, 24)
GREY = (118, 118, 124)
WHITE = (255, 255, 255)
SKY = (70, 120, 180)

# --- bitmap alphabet: 5 wide, 7 tall, '#' marks a filled cell --------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#....", "#....", "#....", "#....", "#....", ".###."),
    "D": ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
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
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "#.#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
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
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", ".#.##", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
}


def measure(s, scale):
    return (len(s) * 6 - 1) * scale if s else 0


def wrap(s, scale, limit):
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if measure(trial, scale) <= limit or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(s, scale, limit):
    while len(s.split()) > 1 and measure(s, scale) > limit:
        s = s.rsplit(" ", 1)[0]
    return s


class Page:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def box(self, x, y, w, h, c):
        for yy in range(y, y + h):
            row = (yy * self.w + x) * 3
            self.px[row:row + w * 3] = bytes(c) * w

    def frame(self, x, y, w, h, c, t=2):
        self.box(x, y, w, t, c)
        self.box(x, y + h - t, w, t, c)
        self.box(x, y, t, h, c)
        self.box(x + w - t, y, t, h, c)

    def circle(self, cx, cy, r, c, ring=False):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (ring and (r - 2) ** 2 < d <= r * r) or \
                        (not ring and d <= r * r):
                    self.set(xx, yy, c)

    def seg(self, x0, y0, x1, y1, c, t=3):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            self.box(x - t // 2, y - t // 2, t, t, c)

    def say(self, x, y, s, scale, c):
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for r in range(7):
                for col in range(5):
                    if glyph[r][col] == "#":
                        self.box(x + col * scale, y + r * scale,
                                 scale, scale, c)
            x += 6 * scale
        return x

    def say_mid(self, cx, y, s, scale, c):
        return self.say(cx - measure(s, scale) // 2, y, s, scale, c)


# --- pictograms, each inside an 84x84 tile at (x, y) ------------------
def pic_tag(pg, x, y, c):
    # price tag with a percent mark: the tariff story
    pg.frame(x + 10, y + 10, 64, 64, c, 4)
    pg.circle(x + 24, y + 24, 5, BRICK)
    pg.say(x + 27, y + 34, "%", 5, c)


def pic_star(pg, x, y, c):
    cx, cy = x + 42, y + 42
    for dx, dy in ((0, -30), (0, 30), (-30, 0), (30, 0),
                   (-21, -21), (21, -21), (-21, 21), (21, 21)):
        pg.seg(cx, cy, cx + dx, cy + dy, GOLD, 4)
    pg.circle(cx, cy, 10, c)


def pic_rocket(pg, x, y, c):
    pg.box(x + 34, y + 10, 16, 44, c)                 # body
    pg.seg(x + 34, y + 12, x + 42, y + 2, c, 4)       # nose
    pg.seg(x + 50, y + 12, x + 42, y + 2, c, 4)
    pg.box(x + 24, y + 44, 8, 14, SKY)                # fins
    pg.box(x + 52, y + 44, 8, 14, SKY)
    pg.circle(x + 42, y + 26, 5, WHITE)               # porthole
    pg.seg(x + 42, y + 58, x + 36, y + 76, BRICK, 4)  # flame
    pg.seg(x + 42, y + 58, x + 48, y + 76, GOLD, 4)


def pic_chip(pg, x, y, c):
    pg.frame(x + 22, y + 22, 40, 40, c, 4)
    pg.say(x + 32, y + 36, "AI", 2, c)
    for k in range(4):
        pg.box(x + 10, y + 28 + k * 10, 12, 3, c)     # pins
        pg.box(x + 62, y + 28 + k * 10, 12, 3, c)
        pg.box(x + 28 + k * 10, y + 10, 3, 12, c)
        pg.box(x + 28 + k * 10, y + 62, 3, 12, c)


def pic_fall(pg, x, y, c):
    pg.seg(x + 10, y + 74, x + 10, y + 10, c, 3)      # axes
    pg.seg(x + 10, y + 74, x + 76, y + 74, c, 3)
    pg.seg(x + 16, y + 22, x + 38, y + 40, BRICK, 4)  # falling line
    pg.seg(x + 38, y + 40, x + 66, y + 62, BRICK, 4)
    pg.seg(x + 66, y + 62, x + 56, y + 62, BRICK, 4)  # arrowhead
    pg.seg(x + 66, y + 62, x + 66, y + 52, BRICK, 4)


def pic_flame(pg, x, y, c):
    pg.box(x + 14, y + 40, 7, 30, c)                  # left stack
    pg.box(x + 63, y + 40, 7, 30, c)                  # right stack
    pg.circle(x + 42, y + 50, 15, BRICK)              # refinery fire
    pg.circle(x + 42, y + 38, 9, GOLD)
    pg.box(x + 12, y + 70, 60, 7, c)                  # plant base


def pic_shield(pg, x, y, c):
    pg.frame(x + 24, y + 10, 36, 48, c, 4)            # shield body
    pg.seg(x + 24, y + 58, x + 42, y + 74, c, 4)
    pg.seg(x + 60, y + 58, x + 42, y + 74, c, 4)
    pg.say(x + 34, y + 26, "20", 2, BRICK)            # the 20 freed


# --- the page ---------------------------------------------------------
# (section, headline, caption, pictogram, accent)
SMALL = [
    ("CHINA - BEIJING", "XI GRAFT PROBE HITS SHANGHAI CHIEF",
     "CHEN JINING INVESTIGATED", pic_star, GOLD),
    ("SPACE - TIANGONG", "PAKISTANI ASTRONAUT BOARDS TIANGONG",
     "FIRST FOREIGNER ON STATION", pic_rocket, SKY),
    ("COURTS - NEW YORK", "HUAWEI CONVICTED IN US TRIAL",
     "GUILTY OF STEALING SECRETS", pic_chip, NAVY),
    ("MARKETS - AI", "ANTHROPIC SLIDES BELOW IPO PRICE",
     "SHARES UNDER $83 POST-LISTING", pic_fall, BRICK),
    ("GULF - ENERGY", "HOUTHIS CLAIM SAUDI REFINERY HIT",
     "BRENT CRUDE TOPS $94", pic_flame, BRICK),
    ("COLOMBIA - BOGOTA", "POLICE FREE 20 HOSTAGES",
     "SUPERMARKET SIEGE ENDS", pic_shield, NAVY),
]


def small_panel(pg, x, y, w, h, num, section, head, caption, pic, accent):
    pg.frame(x, y, w, h, INK, 2)
    pg.box(x, y, w, 6, accent)
    pg.say(x + 108, y + 16, section, 2, BRICK)
    tw = w - 108 - 12
    for j, ln in enumerate(wrap(head, 3, tw)[:2]):
        pg.say(x + 108, y + 40 + j * 26, ln, 3, INK)
    pg.say(x + 108, y + 100, fit(caption, 2, tw), 2, GREY)
    pg.box(x + 108, y + 132, tw, 2, GREY)
    pg.say(x + 108, y + 142, "26 NOV 2026", 2, GREY)
    pg.frame(x + 12, y + 34, 84, 84, GREY, 1)
    pic(pg, x + 12, y + 34, accent)
    pg.say(x + 12, y + 16, "0" + str(num), 2, NAVY)


def render():
    pg = Page(PAGE_W, PAGE_H, CREAM)
    pg.frame(10, 10, PAGE_W - 20, PAGE_H - 20, NAVY, 5)

    # Masthead: navy band, paper name, date line under it.
    pg.box(28, 28, PAGE_W - 56, 96, NAVY)
    pg.say_mid(PAGE_W // 2, 48, "THE WORLD IN ONE DAY", 7, WHITE)
    pg.say_mid(PAGE_W // 2, 132, "THURSDAY 26 NOVEMBER 2026", 3, NAVY)
    pg.box(28, 162, PAGE_W - 56, 3, BRICK)

    # Lead story: one wide panel, big type, tag pictogram on the right.
    lx, ly, lw, lh = 28, 178, PAGE_W - 56, 168
    pg.frame(lx, ly, lw, lh, INK, 3)
    pg.box(lx, ly, lw, 8, BRICK)
    pg.say(lx + 20, ly + 22, "LEAD - TRADE", 2, BRICK)
    for j, ln in enumerate(wrap("US PROPOSES TARIFFS ON 14 PARTNERS",
                                5, lw - 190)[:2]):
        pg.say(lx + 20, ly + 48 + j * 42, ln, 5, INK)
    pg.say(lx + 20, ly + 138, "HIGHEST RATES HIT CHINA ON EXCESS CAPACITY",
           2, GREY)
    pg.frame(lx + lw - 128, ly + 34, 96, 96, GREY, 1)
    pic_tag(pg, lx + lw - 122, ly + 40, NAVY)

    # Six small stories in a 2 x 3 grid.
    gy = 362
    pw, ph, gap = 474, 176, 12
    for i, (section, head, caption, pic, accent) in enumerate(SMALL):
        x = 28 + (i % 2) * (pw + gap)
        y = gy + (i // 2) * (ph + gap)
        small_panel(pg, x, y, pw, ph, i + 1, section, head, caption,
                    pic, accent)

    # Footer: the Thanksgiving line.
    fy = gy + 3 * ph + 2 * gap + 14
    pg.box(28, fy, PAGE_W - 56, 3, NAVY)
    pg.say_mid(PAGE_W // 2, fy + 14,
               "ALSO TODAY: TRUMP SPARES TURKEYS FREEDOM AND FEATHERS",
               2, NAVY)
    pg.say_mid(PAGE_W // 2, fy + 40,
               "THANKSGIVING DAY - 26 NOVEMBER 2026", 2, GREY)
    return pg


def to_png(pg):
    rows = bytearray()
    for yy in range(pg.h):
        rows.append(0)
        start = yy * pg.w * 3
        rows += pg.px[start:start + pg.w * 3]

    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    head = struct.pack(">IIBBBBB", pg.w, pg.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head)
            + chunk(b"IDAT", zlib.compress(bytes(rows), 9))
            + chunk(b"IEND", b""))


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "./out")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "entry.png"), "wb") as fh:
        fh.write(to_png(render()))


if __name__ == "__main__":
    main()
