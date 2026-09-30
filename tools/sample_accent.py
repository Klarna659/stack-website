"""Re-derive --accent from a hero frame — the accent-from-background rule.

Reproduces the algorithm described in index.html's :root comment: take the
saturated pixels (S > .25) of the frame, weighted-circular-mean their hue,
fix chroma at S62%, then walk lightness down until the color clears 4.5:1
against BOTH text surfaces (--paper #FBF7ED and --ground-1 #EFE4CC).

    python tools/sample_accent.py assets/img/home/spill3-frame-first.jpg
"""
import colorsys
import math
import sys

from PIL import Image

PAPER = (0xFB, 0xF7, 0xED)
GROUND1 = (0xEF, 0xE4, 0xCC)


def _chan(c):
    s = c / 255.0
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def lum(rgb):
    r, g, b = rgb
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main(path):
    im = Image.open(path).convert("RGB").resize((320, 180))
    sx = sy = wsum = 0.0
    for r, g, b in im.getdata():
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s > 0.25:
            w = s
            sx += math.cos(h * 2 * math.pi) * w
            sy += math.sin(h * 2 * math.pi) * w
            wsum += w
    if not wsum:
        print("no saturated pixels — frame is grayscale?")
        return
    hue = (math.atan2(sy, sx) / (2 * math.pi)) % 1.0
    print("circular-mean hue: %.1f deg (weight %.0f)" % (hue * 360, wsum))

    # fixed chroma, solve lightness for >=4.5:1 on both surfaces
    for l_pct in range(60, 10, -1):
        rgb = tuple(round(c * 255) for c in
                    colorsys.hls_to_rgb(hue, l_pct / 100.0, 0.62))
        r1, r2 = ratio(rgb, PAPER), ratio(rgb, GROUND1)
        if r1 >= 4.5 and r2 >= 4.5:
            print("--accent: #%02X%02X%02X  (L%d%%, %.2f:1 paper, %.2f:1 ground)"
                  % (*rgb, l_pct, r1, r2))
            # a lighter fill companion at L58%
            fill = tuple(round(c * 255) for c in
                         colorsys.hls_to_rgb(hue, 0.58, 0.55))
            print("--accent-fill: #%02X%02X%02X" % fill)
            return
    print("no lightness clears 4.5:1 at S62 — check the frame")


if __name__ == "__main__":
    main(sys.argv[1])
