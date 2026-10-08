"""Composite the REAL Stack UI onto the phone in a generated frame.

1. Renders the homepage's own CSS-drawn "Your stack" phone screen (the
   chapter-01 .phone-screen div — always in sync with the real app's
   surface) to a PNG via headless Chrome.
2. Perspective-warps it onto the phone's screen quad in the target frame
   and blends a touch of the scene's warmth over it so it sits in the
   photograph instead of floating on it.

Corner coords come from looking at the chosen frame (TL TR BR BL, x,y):

    python tools/comp_screen.py --frame tools/hero_pool/spill_v4/phone_a.png ^
        --out tools/hero_pool/spill_v4/phone_a_ui.png ^
        --quad 300,420 640,400 660,720 310,760
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_PNG = os.path.join(ROOT, "tools", "hero_pool", "spill_v4", "ui_screen.png")

SHOT_SCRIPT = r"""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel='chrome')
    pg = b.new_page(viewport={'width':1440,'height':900}, device_scale_factor=3)
    pg.goto('http://localhost:4321/')
    pg.wait_for_load_state('networkidle')
    pg.wait_for_timeout(1500)
    # the panel lives inside an entrance-fade (.rv) — force it fully
    # opaque or the screenshot catches it mid-fade, washed toward gray
    pg.evaluate("document.querySelectorAll('.rv').forEach(e => {e.style.opacity='1'; e.style.transform='none'})")
    pg.wait_for_timeout(200)
    pg.locator('.phone-screen').screenshot(path=r'%s')
    b.close()
print('ui captured')
"""


def coeffs(src_pts, dst_pts):
    """Perspective transform coefficients mapping dst quad -> src rect
    (PIL's transform wants the inverse mapping)."""
    a = []
    b = []
    for (x, y), (u, v) in zip(dst_pts, src_pts):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b += [u, v]
    return np.linalg.solve(np.array(a, dtype=float),
                           np.array(b, dtype=float)).tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quad", nargs=4, required=True,
                    help="TL TR BR BL as x,y")
    ap.add_argument("--skip-shot", action="store_true")
    a = ap.parse_args()

    if not a.skip_shot or not os.path.exists(UI_PNG):
        code = SHOT_SCRIPT % UI_PNG
        subprocess.run([sys.executable, "-c", code], check=True)

    frame = Image.open(a.frame).convert("RGB")
    ui = Image.open(UI_PNG).convert("RGBA")
    quad = [tuple(map(float, q.split(","))) for q in a.quad]

    w, h = frame.size
    src = [(0, 0), (ui.width, 0), (ui.width, ui.height), (0, ui.height)]
    # warp UI into frame space: build a full-frame RGBA layer
    layer = ui.transform((w, h), Image.PERSPECTIVE,
                         coeffs(src, quad), Image.BICUBIC)

    # warm the UI slightly toward the scene so it doesn't read pasted-on
    warm = ImageEnhance.Color(layer.convert("RGB")).enhance(0.96)
    warm = ImageEnhance.Brightness(warm).enhance(0.97)
    layer = Image.merge("RGBA", (*warm.split(), layer.split()[3]))

    frame = frame.convert("RGBA")
    frame.alpha_composite(layer)
    frame.convert("RGB").save(a.out, "PNG")
    print("saved", a.out)


if __name__ == "__main__":
    main()
