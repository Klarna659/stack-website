"""Build the Open Graph share card out of the page's own hero photograph.

The card that shipped before this was a flat near-black rectangle with a GOLD
rule under the wordmark — the one hue that has been called dead three times —
and it is the single most-seen image the site has: every link anyone pastes into
a message, a forum, a Slack or a tweet renders it. It was also the last place on
the site still speaking the old visual language.

So it is rebuilt from the same three layers the landing page uses: the shipped
hero photograph, the page's scrim over it, and the wordmark on top. Change the
hero and re-run, and the card follows.

Writes assets/img/og-v2.png. It does NOT overwrite og.png, because the live
index.html still points at that one and this session does not touch the live
page.

    python tools/gen_og.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERO = os.path.join(ROOT, "assets", "img", "hero", "hero.jpg")
FONT = os.path.join(ROOT, "assets", "fonts", "InterVariable.ttf")
# JPEG, not PNG. The card is a photograph; the PNG of this exact image was
# 632 KB, which is a slow, sometimes-skipped fetch for every unfurl.
OUT = os.path.join(ROOT, "assets", "img", "og-v2.jpg")

W, H = 1200, 630
INK = (243, 243, 245)
MUT = (170, 176, 184)

TITLE = "Track everything you take."
SUB = "Supplements, peptides, GLP-1 and TRT — one quiet, private app."


def load(path, size, weight):
    """Inter is a variable font with axes [opsz, wght] — IN THAT ORDER.
    set_variation_by_axes takes positional values, so passing [weight] alone
    sets OPTICAL SIZE to 620 (clamped to its 32 maximum) and leaves weight at
    the 400 default. That is why the first card rendered its wordmark in
    Regular. Both axes, always."""
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_axes([min(32.0, max(14.0, float(size))), float(weight)])
    except Exception:
        pass
    return f


def cover(im, w, h, focus=0.5):
    """Fill w x h, cropping the excess, keeping `focus` of the height centred."""
    src_ratio, dst_ratio = im.width / im.height, w / h
    if src_ratio > dst_ratio:                       # source is wider: crop sides
        nh = im.height
        nw = int(nh * dst_ratio)
        x = (im.width - nw) // 2
        box = (x, 0, x + nw, nh)
    else:                                           # source is taller: crop rows
        nw = im.width
        nh = int(nw / dst_ratio)
        y = int((im.height - nh) * focus)
        box = (0, y, nw, y + nh)
    return im.crop(box).resize((w, h), Image.LANCZOS)


def scrim(size, stops):
    """The page's own gradient, as an alpha mask over black."""
    w, h = size
    layer = Image.new("L", (1, h))
    px = layer.load()
    for y in range(h):
        t = y / float(h - 1)
        a = stops[0][1]
        for i in range(len(stops) - 1):
            t0, a0 = stops[i]
            t1, a1 = stops[i + 1]
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0) if t1 > t0 else 0
                a = a0 + (a1 - a0) * f
                break
        px[0, y] = int(round(a * 255))
    return layer.resize((w, h))


def main():
    im = cover(Image.open(HERO).convert("RGB"), W, H, focus=0.42)

    # The landing page's scrim, plus a little extra on the left where the
    # wordmark and title sit. Same idea as the page: darken where type lands,
    # leave the photograph alone everywhere else.
    mask = scrim((W, H), [(0.0, .38), (0.30, .34), (0.55, .40), (1.0, .72)])
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, mask)

    side = Image.new("L", (W, 1))
    sp = side.load()
    for x in range(W):
        t = x / float(W - 1)
        sp[x, 0] = int(round(max(0.0, 0.34 * (1.0 - t / 0.72)) * 255))
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)),
                         im, side.resize((W, H)))

    d = ImageDraw.Draw(im)

    # The three-disc mark, at the proportions the site's SVG uses.
    cx, cy, rx, ry, gap = 96, 300, 38, 10, 23
    for i, fill in enumerate(((138, 140, 148), (74, 74, 82), (243, 243, 245))):
        y = cy + (i - 1) * gap
        d.ellipse([cx - rx, y - ry, cx + rx, y + ry], fill=fill)

    d.text((150, 300), "Stack", font=load(FONT, 62, 620), fill=INK, anchor="lm")
    d.text((58, 404), TITLE, font=load(FONT, 54, 600), fill=INK, anchor="lt")
    d.text((58, 480), SUB, font=load(FONT, 25, 420), fill=MUT, anchor="lt")

    im.save(OUT, "JPEG", quality=88, optimize=True, progressive=True)
    print("%s  %sx%s  %.1f KB"
          % (os.path.basename(OUT), W, H, os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    main()
