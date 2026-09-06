"""Cut the settled bottle out of the hero's last video frame.

The "depth trick" hero layering needs a sharp, transparent cutout of the
tipped-over bottle (plus the capsules spilling right at its mouth) from
assets/img/home/spill2-frame-last.jpg, positioned so it lands in EXACTLY
the same screen spot the bottle occupies in the video — at any viewport
size — once it fades in above the headline at the handoff moment.

The trick for pixel-perfect alignment without per-viewport math: export the
cutout on a transparent canvas at the SAME dimensions as the source frame
(1280x720), then apply the identical CSS the video/bg-img already use
(object-fit:cover; object-position:63% 50%). Because it's the same source
resolution cropped by the same rule, the browser lands the bottle in the
same spot the video left it in, with zero coordinate math or breakpoints.

    NUMBA_DISABLE_JIT=1 python tools/gen_bottle_cutout.py
"""
import os

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "img", "home", "spill3-frame-last.jpg")
OUT = os.path.join(ROOT, "assets", "img", "home", "bottle-settled-cut.png")

# Crop the bottle + cap first, so rembg targets just that object instead of
# guessing across the whole 1280x720 stone-counter scene (the separately-
# scattered tablets on the left that the CSS pill sprites already own).
# v2 (spill3): bottle x~660-1070, cap x~1010-1210, y~250-540.
BBOX = (640, 230, 1240, 560)
FEATHER_PX = 1.5


def main():
    full = Image.open(SRC).convert("RGB")
    W, H = full.size
    crop = full.crop(BBOX)

    from rembg import remove, new_session
    session = new_session("u2net")
    cut = remove(crop, session=session, alpha_matting=True,
                 alpha_matting_foreground_threshold=240,
                 alpha_matting_background_threshold=10,
                 alpha_matting_erode_size=8)
    cut = cut.convert("RGBA")

    arr = np.array(cut)
    alpha = arr[:, :, 3]

    # 1) largest connected component only — drops flecked rembg noise
    #    (stray glare pixels, a fingernail of the far window) so the only
    #    shape left is the bottle+capsules blob itself.
    mask = alpha > 20
    labeled, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(mask, labeled, range(1, n + 1))
        keep = np.argmax(sizes) + 1
        mask = labeled == keep
        alpha = np.where(mask, alpha, 0).astype(np.uint8)

    # 2) fill holes — the bottle's amber glass is translucent enough that
    #    rembg sometimes punches a hole through to the "background" alpha
    #    inside the glass; a solid silhouette reads as an object, a
    #    Swiss-cheese one reads as a bug.
    filled = ndimage.binary_fill_holes(alpha > 20)
    alpha = np.where(filled, np.maximum(alpha, 255), 0).astype(np.uint8)

    arr[:, :, 3] = alpha
    cut = Image.fromarray(arr, "RGBA")

    # 3) feather — a hard rembg edge on a photographic cutout looks cut out;
    #    a 1.5px blur of the alpha channel only (not the RGB) softens the
    #    silhouette edge to match the source photo's own lens softness.
    a_im = Image.fromarray(alpha, "L").filter(
        ImageFilter.GaussianBlur(FEATHER_PX))
    cut.putalpha(a_im)

    # Composite back onto a full-frame transparent canvas at the crop's
    # original position — this is what makes the CSS object-position math
    # line up with the video/bg-img automatically, at every viewport size.
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(cut, dest=(BBOX[0], BBOX[1]))
    canvas.save(OUT, "PNG", optimize=True)

    nz = np.array(canvas)[:, :, 3]
    print("saved", OUT, canvas.size,
          "opaque px:", int((nz > 200).sum()),
          "/ total:", nz.size,
          "(%.1f%%)" % (100.0 * (nz > 20).sum() / nz.size))


if __name__ == "__main__":
    main()
