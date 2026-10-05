#!/usr/bin/env python3
"""Regenerate assets/img/social-card.png, the 1200x630 image that LinkedIn,
Slack, WhatsApp and the like show when the site's link is posted.

The title, date, time and venue are read from _config.yml, so run this after
changing any of them:

    pip install pillow font-hanken-grotesk
    python3 tools/social_card.py

The icon comes from assets/img/apple-touch-icon.png and the logo from
assets/img/aim-logo.png. Text is set in Hanken Grotesk (OFL), shipped by the
font-hanken-grotesk package.
"""
import re
from pathlib import Path

import font_hanken_grotesk
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
IMG = REPO / "assets/img"
OUT = IMG / "social-card.png"
FONTS = Path(font_hanken_grotesk.__file__).parent / "files"

# Read the workshop facts from _config.yml without needing a YAML library.
cfg = (REPO / "_config.yml").read_text()


def val(key):
    return re.search(rf'^\s*{key}:\s*"([^"]*)"', cfg, re.M).group(1)


title = val("title")
date = val("date")
start, end = [t.strip() for t in val("time").split("-")]
venue = f'{val("venue_full")}, Amsterdam'

W, H = 1200, 630
BG = (251, 252, 253)
ACCENT = (47, 111, 159)
INK = (31, 41, 51)
MUTED = (76, 89, 106)
VENUE = (60, 75, 93)
LEFT = 86

im = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(im)

# Left accent bar with a slight vertical gradient, as on the page.
top, bottom = (47, 111, 159), (47, 137, 153)
for y in range(H):
    t = y / (H - 1)
    draw.line([(0, y), (14, y)],
              fill=tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))

# App icon, top right: the touch icon with rounded corners.
size, radius = 110, 16
icon = Image.open(IMG / "apple-touch-icon.png").convert("RGB").resize((size, size), Image.LANCZOS)
mask = Image.new("L", (size, size), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
im.paste(icon, (1021, 60), mask)


def font(weight, size):
    return ImageFont.truetype(str(FONTS / f"HankenGrotesk-{weight}.otf"), size)


def spaced(x, y, text, f, fill, spacing):
    """Draw text with extra letter spacing, anchored on the baseline."""
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += draw.textlength(ch, font=f) + spacing


# A "Something:" prefix in the title becomes the kicker; the rest is the title.
kicker, _, main = title.rpartition(": ")
if not main:
    kicker, main = "Workshop", title
spaced(LEFT, 89, kicker.upper(), font("Bold", 20), ACCENT, 3.2)

# Title on two lines, breaking before the last three words.
words = main.split()
line1, line2 = " ".join(words[:-3]), " ".join(words[-3:])
tf = font("Bold", 74)
draw.text((LEFT, 263), line1, font=tf, fill=INK, anchor="ls")
draw.text((LEFT, 339), line2, font=tf, fill=INK, anchor="ls")

# Date line: bold date, then a muted separator and the time range.
df, rf = font("Bold", 28), font("Regular", 28)
draw.text((LEFT, 410), date, font=df, fill=INK, anchor="ls")
x = LEFT + draw.textlength(date, font=df)
draw.text((x, 410), f" · {start}–{end}", font=rf, fill=MUTED, anchor="ls")

# Venue line
draw.text((LEFT, 449), venue, font=rf, fill=VENUE, anchor="ls")

# AIM logo, bottom left, 60px tall.
logo = Image.open(IMG / "aim-logo.png").convert("RGBA")
h = 60
logo = logo.resize((round(logo.width * h / logo.height), h), Image.LANCZOS)
im.paste(logo, (LEFT, 514), logo)

im.save(OUT, optimize=True)
print(f"wrote {OUT.relative_to(REPO)} ({W}x{H})")
