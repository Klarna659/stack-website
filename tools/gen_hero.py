"""Generate the landing page's hero background locally with FLUX.

Same machine, same model and same sampler settings the app's grounds were made
with (`dose_tracker/tools/gen_backgrounds.py`), so the site and the app come out
of one image pipeline rather than two. Original images on Sim's own 5070 Ti —
no licence, no attribution, no stock tell.

WHAT IS DIFFERENT FROM THE APP'S GROUNDS
----------------------------------------
The app's grounds are 768x1664 portrait, composed against a mask of where the
phone UI leaves the photograph visible. A web hero has the opposite problem: it
is a wide letterbox on a desktop and a tall crop on a phone, and it has to hold
big type in the middle of the frame in both.

The composition rule survives the change, though, and for the same reason: LOW
horizon, subject in the bottom third, a vast empty gradient sky above it. The
empty sky is what the headline sits on, and an unbroken gradient is the best
possible thing to put 60px of white on. Centre-cropping that to portrait on a
phone still leaves sky over subject, which is why it works in both shapes.

Generated at 1920x1080 — about 2MP, near the top of what flux-dev stays
coherent at — then Lanczos-upscaled to 3840x2160. These are smooth atmospheric
gradients with no fine texture to invent, so the upscale is invisible and the
4K JPEG still lands small.

    python tools/gen_hero.py            generate the whole pool
    python tools/gen_hero.py ridge      just one
    python tools/gen_hero.py --ship ridge_a=hero
    python tools/gen_hero.py --gate            check the SHIPPED hero carries
                                               every piece of hero type
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8188"
COMFY_OUT = r"C:\AI\ComfyUI_windows_portable\ComfyUI\output"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "tools", "hero_pool")
DEST = os.path.join(ROOT, "assets", "img", "hero")

W, H = 1920, 1080          # generate here
UP_W, UP_H = 3840, 2160    # ship here

# flux-dev at cfg 1.0 ignores the negative conditioning entirely — it is wired
# up because the sampler wants the input, not because it does anything. Every
# exclusion that matters has to be stated positively in the prompt itself.
NEGATIVE = ("text, watermark, people, buildings, oversaturated, hdr, "
            "blown highlights, lens flare, cluttered")

# ⚠ THE FIRST POOL WAS WRONG, AND THE PROMPT WAS WHY
#
# v1 of this file inherited the app's composition rule verbatim: "a vast empty
# gradient sky filling the entire upper two thirds with no clouds and no
# detail". On a phone, behind a day strip and a card, that rule is correct —
# there is barely any photograph visible and what shows must not fight 11px
# type. On a 4K website hero it produces exactly what Sim called it: an empty
# blue rectangle. The rule was solving the app's problem on the site's canvas.
#
# So the brief inverts. The web hero wants a real PLACE with depth, texture and
# a foreground, and legibility is bought with tone and scrim instead of with
# emptiness: aim DARK (0.22-0.34 rather than 0.38-0.68), put the detail in the
# lower half where no headline lands, and let the top stay atmospheric — haze,
# fog, falling light — rather than blank.

COMMON = (
    "atmospheric landscape photograph, deep layered depth, real texture and "
    "detail in the foreground, moody low light after sunset, cool shadows, "
    "detail retained in the shadows, no crushed blacks, volumetric haze, "
    "deserted, no people, no text, subtle film grain, muted cinematic colour "
    "grade, shot on medium format with a wide lens, quiet and expensive"
)

HEROES = {
    # A place, with something in it. The upper third stays soft — haze, fog,
    # falling light — so the headline still has somewhere to sit.
    "pines": ("a dense misty pine forest on a mountainside seen from above, "
              "ridges of trees receding into fog layer after layer, cold blue "
              "dusk light raking across the tops, " + COMMON),
    "canyon": ("a deep sandstone canyon at dusk, sculpted walls in shadow with "
               "one soft shaft of light falling down the far wall, the river "
               "bend dark at the bottom of the frame, " + COMMON),
    "alpine": ("a still alpine lake at dusk, dark pine shoreline in the "
               "foreground, snow peaks reflected in the water, mist sitting on "
               "the surface, " + COMMON),
    "fjord": ("a steep fjord wall dropping into dark water, low cloud caught "
              "halfway up the cliffs, layers of headland receding into rain "
              "haze, " + COMMON),
    "mesa": ("desert mesas at blue hour, textured rock in the near foreground, "
             "buttes receding into dust haze, the last warm light on the "
             "highest edges, " + COMMON),
    "storm": ("a wide plain under a heavy cloud ceiling at dusk, rain falling "
              "in the distance, low ridges catching a break of light, "
              + COMMON),
}

SEEDS = {"pines": (604118, 118207), "canyon": (330415, 907712),
         "alpine": (229740, 441903), "fjord": (471692, 550118),
         "mesa": (693351, 812440), "storm": (358204, 815036)}


def graph(prompt, seed):
    return {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"}},
        "2": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"text": NEGATIVE, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage",
              "inputs": {"width": W, "height": H, "batch_size": 1}},
        "5": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": 28, "cfg": 1.0,
                         "sampler_name": "euler", "scheduler": "simple",
                         "denoise": 1.0, "model": ["1", 0], "positive": ["2", 0],
                         "negative": ["3", 0], "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode",
              "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "stackhero", "images": ["6", 0]}},
    }


def submit(g):
    data = json.dumps({"prompt": g}).encode()
    req = urllib.request.Request(BASE + "/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))["prompt_id"]
    except urllib.error.HTTPError as e:
        print("REJECTED:", e.read().decode()[:1200], flush=True)
        raise


def wait(pid, timeout=1800):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            h = json.load(urllib.request.urlopen(
                "%s/history/%s" % (BASE, pid), timeout=30))
        except Exception:
            time.sleep(2)
            continue
        if pid in h:
            node = h[pid]
            if node.get("outputs"):
                return node
            for m in node.get("status", {}).get("messages", []):
                if m and m[0] in ("execution_error", "execution_interrupted"):
                    print("EXEC ERROR:", json.dumps(m)[:1200], flush=True)
                    return None
        time.sleep(2)
    raise TimeoutError(pid)


def collect(hist):
    for _, out in (hist.get("outputs") or {}).items():
        for it in out.get("images", []):
            src = os.path.join(COMFY_OUT, it.get("subfolder", ""), it["filename"])
            if os.path.exists(src):
                return src
    return None


def sky_flatness(path):
    """How empty the top two thirds are.

    The headline sits there, so detail up there is not atmosphere, it is noise
    competing with 60px of white type. Reported as the mean absolute row-to-row
    luminance step across the upper 62% — lower is better.
    """
    from PIL import Image, ImageStat
    im = Image.open(path).convert("L")
    w, h = im.size
    top = im.crop((0, 0, w, int(h * 0.62))).resize((160, 160))
    px = list(top.getdata())
    rows = [sum(px[r * 160:(r + 1) * 160]) / 160.0 for r in range(160)]
    steps = [abs(rows[i + 1] - rows[i]) for i in range(len(rows) - 1)]
    detail = ImageStat.Stat(top).stddev[0]
    return {"row_step": round(sum(steps) / len(steps), 3),
            "sky_stddev": round(detail, 2)}


def tone(path):
    """Mean luminance of the whole frame, 0-1. The app targets 0.34."""
    from PIL import Image, ImageStat
    im = Image.open(path).convert("L").resize((240, 135))
    return round(ImageStat.Stat(im).mean[0] / 255.0, 3)


def generate(names):
    os.makedirs(POOL, exist_ok=True)
    made = []
    for name in names:
        for i, seed in enumerate(SEEDS[name]):
            tag = "%s_%s" % (name, "ab"[i])
            out = os.path.join(POOL, tag + ".png")
            if os.path.exists(out):
                print("skip", tag, flush=True)
                made.append(out)
                continue
            t0 = time.time()
            pid = submit(graph(HEROES[name], seed))
            hist = wait(pid)
            src = collect(hist) if hist else None
            if not src:
                print("FAILED", tag, flush=True)
                continue
            from PIL import Image
            Image.open(src).save(out)
            print("%-10s %5.0fs  tone %.3f  %s"
                  % (tag, time.time() - t0, tone(out), sky_flatness(out)),
                  flush=True)
            made.append(out)
    return made


# flux occasionally lays a few rows of garbage along an edge — a sliver of
# colour noise at the top, or baked-in letterbox bars on the cinematic prompts.
# It is invisible in a 1920px preview and very visible stretched to 4K behind a
# headline, so every shipped image loses its outermost rows first.
EDGE_CROP = 0.012


def ship(pairs):
    """Upscale a chosen pool image to 4K and write the responsive set."""
    from PIL import Image
    os.makedirs(DEST, exist_ok=True)
    for pair in pairs:
        tag, name = pair.split("=")
        src = os.path.join(POOL, tag + ".png")
        im = Image.open(src).convert("RGB")
        w, h = im.size
        dx, dy = int(w * EDGE_CROP), int(h * EDGE_CROP)
        im = im.crop((dx, dy, w - dx, h - dy))
        big = im.resize((UP_W, UP_H), Image.LANCZOS)
        # Three widths. A phone has no business downloading 4K to put a scrim
        # over it, and srcset means it does not have to.
        # A DPR-3 phone renders a 390px box (x1.09 for the drift) = ~1275 device px.
        # With only 960w and 1920w to choose from it takes the 1920 — 2.27x the
        # pixels it needs, ~92 KB wasted on the LCP of the most common device
        # class there is. 1280w is the candidate that was missing.
        for w, q, suffix in ((UP_W, 82, ""), (1920, 84, "-1920"),
                             (1280, 84, "-1280"), (960, 84, "-960")):
            out = os.path.join(DEST, "%s%s.jpg" % (name, suffix))
            (big if w == UP_W else big.resize(
                (w, round(UP_H * w / UP_W)), Image.LANCZOS)
             ).save(out, "JPEG", quality=q, optimize=True, progressive=True)
            print("%-28s %6.1f KB  %sx%s"
                  % (os.path.basename(out), os.path.getsize(out) / 1024.0,
                     w, round(UP_H * w / UP_W)), flush=True)



# ── THE LEGIBILITY GATE ────────────────────────────────────────────────────
# The first version of this file scored a candidate on ONE number: white type on
# the brightest row of a single band. That number said the shipped ground was
# 7.05:1 and it was wrong — not miscalculated, just measuring the wrong thing.
# It sampled a band the headline does not sit in, ignored the tinted band at the
# top of the page, ignored the text scrim entirely, and never looked at the 11px
# eyebrow, which is the hardest element on the page because small text needs
# 4.5:1 rather than 3. Composited properly, that "7.05:1" ground put the eyebrow
# at 1.67:1.
#
# So the gate now reproduces the page's actual layer stack — ground, tinted
# band, page scrim, text scrim — and checks EVERY piece of type in the hero at
# the size and weight it is really drawn, at the position it really occupies.
# Constants below mirror index-v2.html; if you change them there, change them
# here, and vice versa.
#
#     python tools/gen_hero.py --gate                  the shipped hero
#     python tools/gen_hero.py --gate alpine_b         a candidate from the pool

BAND_RGB = (0x2C, 0x3C, 0x47)
BAND_H, BAND_OP, BAND_HOLD = 0.30, 0.94, 0.52
PAGE_SCRIM = [(0.00, .34), (0.26, .30), (0.48, .26), (0.72, .42), (0.92, .90), (1.00, 1.0)]
TEXT_SCRIM = [(0.00, .28), (0.30, .28), (0.50, .30), (0.60, .10), (0.82, .00), (1.00, .00)]

# (name, top, bottom, text alpha, required ratio) as fractions of the hero stage.
HERO_TYPE = [
    ("eyebrow 11px",    0.20, 0.28, 0.86, 4.5),
    ("h1 40-80px",      0.28, 0.41, 1.00, 3.0),
    ("statement 17px",  0.41, 0.48, 0.86, 4.5),
    ("buttons 15px",    0.49, 0.58, 1.00, 4.5),
    ("email field",     0.58, 0.66, 1.00, 4.5),
    ("hero note 13px",  0.65, 0.71, 0.86, 4.5),
    ("proof line 13px", 0.71, 0.79, 0.86, 4.5),
]


def _ramp(stops, t):
    for i in range(len(stops) - 1):
        t0, a0 = stops[i]
        t1, a1 = stops[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return a0 + (a1 - a0) * f
    return stops[-1][1]


def _band(t):
    if t >= BAND_H:
        return 0.0
    u = t / BAND_H
    return BAND_OP * (1.0 if u <= BAND_HOLD else (1 - (u - BAND_HOLD) / (1 - BAND_HOLD)))


def _over(fg, bg, a):
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))


def gate(path):
    """Composite the page's real layers and check every piece of hero type."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    W, H = im.size
    rows = []
    ok = True
    for name, t0, t1, alpha, need in HERO_TYPE:
        worst = None
        for k in range(11):
            ty = t0 + (t1 - t0) * k / 10.0
            for j in range(17):
                tx = 0.06 + 0.88 * j / 16.0
                px = im.getpixel((min(W - 1, int(W * tx)), min(H - 1, int(H * ty))))
                c = _over(BAND_RGB, px, _band(ty))
                c = _over((0, 0, 0), c, _ramp(PAGE_SCRIM, ty))
                c = _over((0, 0, 0), c, _ramp(TEXT_SCRIM, ty))
                fg = _over((255, 255, 255), c, alpha)
                lo, hi = sorted((luminance(*c), luminance(*fg)))
                r = (hi + 0.05) / (lo + 0.05)
                if worst is None or r < worst:
                    worst = r
        rows.append((name, worst, need, worst >= need))
        ok = ok and worst >= need
    print("%-18s %8s %6s" % ("hero element", "ratio", "needs"))
    print("-" * 36)
    for name, r, need, good in rows:
        print("%-18s %7.2f:1 %6.1f  %s" % (name, r, need, "pass" if good else "FAIL"))
    print()
    print("GATE PASS" if ok else "GATE FAIL - this ground cannot carry the hero type")
    return ok

def main():
    args = [a for a in sys.argv[1:]]
    if args and args[0] == "--ship":
        ship(args[1:])
        return
    if args and args[0] == "--gate":
        target = args[1] if len(args) > 1 else None
        src = (os.path.join(POOL, target + ".png") if target
               else os.path.join(DEST, "hero.jpg"))
        raise SystemExit(0 if gate(src) else 1)
    if args and args[0] == "--rank":
        for f in sorted(os.listdir(POOL)):
            if f.endswith(".png"):
                p = os.path.join(POOL, f)
                print("%-12s tone %.3f  %s" % (f[:-4], tone(p), sky_flatness(p)))
        return
    generate(args or list(HEROES))



def headline_contrast(path, band=(0.30, 0.72)):
    """WCAG ratio for white type over the scrimmed hero band.

    The hero's headline sits in the vertical middle of the stage, which on this
    page is roughly 30-72% down. The page paints a gradient scrim over the
    photograph before any type lands on it, so measuring the raw image is
    meaningless — this composites the same scrim first, then reports the ratio
    against the BRIGHTEST row in the band, which is the row that has to hold.

    3.0:1 is the WCAG floor for large text (>=24px). The headline is 40-80px.
    """
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    im = im.resize((160, round(160 * h / w)))
    W, H = im.size
    px = im.load()
    worst = None
    for y in range(int(H * band[0]), int(H * band[1])):
        t = y / float(H)
        a = scrim_alpha_at_page(t)
        lum = 0.0
        for x in range(0, W, 2):
            r, g, b = px[x, y]
            r, g, b = r * (1 - a), g * (1 - a), b * (1 - a)
            lum += luminance(r, g, b)
        lum /= len(range(0, W, 2))
        ratio = 1.05 / (lum + 0.05)
        if worst is None or ratio < worst:
            worst = ratio
    return round(worst, 2)


# The page's own scrim stops, mirrored from landing-v2.html.
PAGE_STOPS = [0.00, 0.26, 0.48, 0.72, 0.92, 1.00]
PAGE_ALPHAS = [0.34, 0.30, 0.26, 0.42, 0.90, 1.00]


def scrim_alpha_at_page(t):
    for i in range(len(PAGE_STOPS) - 1):
        if PAGE_STOPS[i] <= t <= PAGE_STOPS[i + 1]:
            f = (t - PAGE_STOPS[i]) / (PAGE_STOPS[i + 1] - PAGE_STOPS[i])
            return PAGE_ALPHAS[i] + (PAGE_ALPHAS[i + 1] - PAGE_ALPHAS[i]) * f
    return PAGE_ALPHAS[-1]


def _chan(c):
    s = c / 255.0
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def luminance(r, g, b):
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)


# ⚠ THIS MUST STAY LAST IN THE FILE. It used to sit mid-module, so every helper
# appended after it — luminance(), headline_contrast(), the gate — did not exist
# yet when main() ran, and any CLI path touching them died with a NameError.
# Importing the module hid it completely, which is why it survived.
if __name__ == "__main__":
    main()
