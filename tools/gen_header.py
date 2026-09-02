"""Generate the site's header photographs locally with FLUX, and prove they FIT.

Generated on Sim's own 5070 Ti through ComfyUI: original images tuned to this
exact layout, no licence, no attribution, no stock tell. Same rig and the same
hard-won rules as the app's grounds (`dose_tracker/tools/gen_backgrounds.py`);
what is different is the geometry, because a landing page and a phone screen
put their text in completely different places.

═══════════════════════════════════════════════════════════════════════════
WHY THE SITE NEEDS THIS AT ALL
═══════════════════════════════════════════════════════════════════════════
The app is photographic -- a real dusk landscape under an opaque chrome band,
which is the thing that makes it read like Oura instead of like a side
project. The website is flat black with a gold serif flourish. They do not
look like the same company, and the site is the half that looks generated.

═══════════════════════════════════════════════════════════════════════════
THE TWO RULES THAT ALREADY COST TIME ONCE
═══════════════════════════════════════════════════════════════════════════
1.  YOU CANNOT ASK FLUX-DEV TO CAP ITS HIGHLIGHTS. It runs at guidance 1.0 and
    effectively ignores the negative prompt -- "no bright sky" comes back with
    a sky at 0.99. Enforce it AFTER generation with a linear multiply in
    linear light: luminance is a linear combination of linear-light channels,
    so scaling all three by k scales luminance by exactly k, and the picture
    keeps its gradient and simply arrives a couple of stops down. Which is
    what dusk looks like anyway.

2.  MEASURE EVERY BAND THAT CARRIES TEXT, and sample the BRIGHTEST patch in
    it rather than the average -- a mean hides a sun in one corner, and that
    corner is exactly where a word disappears. Stride 2, not 4: a coarser grid
    steps straight over a thin bright horizon.

═══════════════════════════════════════════════════════════════════════════
AND THE CALM SCORE, WHICH IS THE OPPOSITE OF THE APP'S
═══════════════════════════════════════════════════════════════════════════
The app wants its subject in the gaps between UI. A landing page wants the
reverse: a QUIET region where the headline sits, and detail everywhere else,
so the picture is unmistakably a photograph and the type is still the loudest
thing on the screen. `calm_score()` measures edge energy inside the headline
box against edge energy outside it. High score = a place to put words.

Usage:
    python tools/gen_header.py                 generate the pool
    python tools/gen_header.py ridge coast     just these
    python tools/gen_header.py --rank          score the pool
    python tools/gen_header.py --ship ridge    upscale a winner to 4K + web
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8188"
COMFY_OUT = r"C:\AI\ComfyUI_windows_portable\ComfyUI\output"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "mockups", "assets", "pool")
SHIP = os.path.join(ROOT, "mockups", "assets", "img")

# 16:9, and both multiples of 16 -- flux wants that and 1080 is not one.
# 2.1MP is about where flux-dev stops inventing a second horizon.
W, H = 1920, 1088

# Two stops down from the app's phone grounds. A header carries a headline at
# 64-96px, not an 11px day strip, so it can afford to be brighter -- but the
# nav sits ON it, so not by much.
TONE_TARGET = 0.38
SHADOW_LIFT = 0.012

FLOOR_LARGE = 3.0    # >=24px, or >=18.66px bold
FLOOR_BODY = 4.5

# The bands a LANDING PAGE puts text in, as fractions of height. Nothing like
# the phone's, which is the whole reason this file is not a flag on the other
# one.
BANDS = [
    (0.00, 0.09, FLOOR_BODY,  "nav"),
    (0.30, 0.66, FLOOR_LARGE, "headline"),
    (0.66, 0.82, FLOOR_BODY,  "sub + buttons"),
]
# Where the headline actually sits: left 58%, vertically 0.30-0.82. The
# picture should be QUIET here and busy outside it.
CALM_BOX = (0.02, 0.28, 0.58, 0.84)

NEGATIVE = ("blown highlights, white sky, overexposed, harsh sun, text, "
            "watermark, logo, caption, people, buildings, road, signage")

STYLE = ("shot on a medium format camera, 35mm, deep depth of field, "
         "muted cold blue-grey palette, heavy atmosphere, fine grain, "
         "no people, no structures, natural light only")

PROMPTS = {
    "ridge": ("A vast dark mountain ridge at blue hour under low dragging "
              "cloud, a wide empty gravel plain in the foreground, one thin "
              "warm break of light along the ridgeline, " + STYLE),
    "coast": ("A cold northern coastline at dusk, long exposure water gone "
              "to smooth grey mist over black rock, a low headland far off, "
              "overcast, " + STYLE),
    "dune": ("Soft desert dunes at last light, long blue shadows across the "
             "sand, an enormous quiet sky, minimal and almost abstract, "
             + STYLE),
    "fog": ("Layered forested ridges receding into cold fog, each ridge "
            "paler than the one before, dusk, no sky visible, " + STYLE),
    "salt": ("A vast salt flat at dusk under a thin sheen of standing water "
             "reflecting a dim overcast sky, cracked pale ground, utterly "
             "empty to the horizon, " + STYLE),
}
SEEDS = {"ridge": 118804, "coast": 447215, "dune": 903366,
         "fog": 271940, "salt": 655128}


# ── ComfyUI ───────────────────────────────────────────────────────────────

def graph(prompt, seed, upscale=False):
    g = {
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
    }
    out = ["6", 0]
    if upscale:
        # 4x-UltraSharp then back down to 3840 wide. Upscaling past the target
        # and resampling down is what makes a 4K header look photographed
        # rather than enlarged -- a straight Lanczos 2x is visibly soft.
        g["8"] = {"class_type": "UpscaleModelLoader",
                  "inputs": {"model_name": "4x-UltraSharp.pth"}}
        g["9"] = {"class_type": "ImageUpscaleWithModel",
                  "inputs": {"upscale_model": ["8", 0], "image": ["6", 0]}}
        g["10"] = {"class_type": "ImageScale",
                   "inputs": {"upscale_method": "lanczos", "width": 3840,
                              "height": 2176, "crop": "disabled",
                              "image": ["9", 0]}}
        out = ["10", 0]
    g["7"] = {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "stackhdr", "images": out}}
    return g


def submit(g):
    data = json.dumps({"prompt": g}).encode()
    req = urllib.request.Request(BASE + "/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))["prompt_id"]
    except urllib.error.HTTPError as e:
        print("REJECTED:", e.read().decode()[:1200], flush=True)
        raise


def wait(pid, timeout=2400):
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


# ── colour maths ──────────────────────────────────────────────────────────

def _chan(c):
    s = c / 255.0
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def _srgb(lin):
    lin = max(0.0, min(1.0, lin))
    v = lin * 12.92 if lin <= 0.0031308 else 1.055 * (lin ** (1 / 2.4)) - 0.055
    return max(0, min(255, int(round(v * 255))))


def luminance(r, g, b):
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)


def tone_cap(img, target=TONE_TARGET):
    """Expose down until the brightest pixel lands at `target`, then lift the
    floor so the shadows are a base density rather than a pit."""
    w, h = img.size
    px = img.load()
    peak = 0.0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            lu = luminance(*px[x, y][:3])
            if lu > peak:
                peak = lu
    k = 1.0 if (peak <= target or peak <= 0) else target / peak
    lut = []
    for v in range(256):
        lin = _chan(v) * k
        lin = SHADOW_LIFT + (1 - SHADOW_LIFT) * lin
        lut.append(_srgb(lin))
    return img.point(lut * 3), k


def measure(path):
    """The brightest patch in every band that carries text, and the contrast
    white would get on it. Brightest, not mean -- see the header note."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    rows = []
    for t0, t1, floor, name in BANDS:
        y0, y1 = int(t0 * h), int(t1 * h)
        peak = 0.0
        # 24px blocks: a patch the size of a letter, not a pixel
        step = max(2, w // 160)
        for y in range(y0, y1, step):
            for x in range(0, w, step):
                lu = luminance(*px[x, y])
                if lu > peak:
                    peak = lu
        ratio = 1.05 / (peak + 0.05)
        rows.append({"band": name, "peak": round(peak, 3),
                     "contrast": round(ratio, 2), "floor": floor,
                     "ok": ratio >= floor})
    return rows


def _edges(im, box=None):
    """Mean absolute gradient -- how much is going on in a region."""
    g = im.convert("L")
    w, h = g.size
    px = g.load()
    x0, y0, x1, y1 = box or (0, 0, w, h)
    tot, n = 0, 0
    for y in range(int(y0), int(y1) - 2, 3):
        for x in range(int(x0), int(x1) - 2, 3):
            v = px[x, y]
            tot += abs(px[x + 2, y] - v) + abs(px[x, y + 2] - v)
            n += 1
    return tot / max(1, n)


def calm_score(path):
    """Quiet where the headline goes, busy everywhere else.

    Returns the ratio of outside-energy to inside-energy. Above ~1.4 means the
    picture is actually leaving you somewhere to put words; below 1.0 means
    the busiest thing on the page is directly behind the headline.
    """
    from PIL import Image
    im = Image.open(path).convert("L")
    w, h = im.size
    bx = (CALM_BOX[0] * w, CALM_BOX[1] * h, CALM_BOX[2] * w, CALM_BOX[3] * h)
    inside = _edges(im, bx)
    whole = _edges(im)
    # outside = whole minus the box's share, approximately but monotonically
    return round((whole + 1e-6) / (inside + 1e-6), 3)


def accent_from(path):
    """The accent, SAMPLED FROM THE PHOTOGRAPH rather than picked.

    This is the product's own idea: in the app the accent is derived from
    whichever background the user chooses, so it is different per person. The
    site doing the same thing to its own header is the same rule applied one
    level up -- and it is why these three directions do not share a hue.

    Takes the most saturated pixels in the upper half (the sky's warm break,
    the water's cold cast), averages them, then pushes the result to a fixed
    lightness and saturation so it is legible as a link colour on near-black.
    """
    import colorsys
    from PIL import Image
    im = Image.open(path).convert("RGB").resize((240, 136))
    px = im.load()
    best = []
    for y in range(0, 100):
        for x in range(240):
            r, g, b = px[x, y]
            hh, ll, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if ss > 0.08 and 0.06 < ll < 0.75:
                best.append((ss, hh, ss, ll))
    if not best:
        return "#7FA8C9"
    best.sort(reverse=True)
    top = best[:max(12, len(best) // 20)]
    # circular mean of hue, or red-ish wraps to cyan
    import math
    sx = sum(math.cos(2 * math.pi * t[1]) for t in top)
    sy = sum(math.sin(2 * math.pi * t[1]) for t in top)
    hue = (math.atan2(sy, sx) / (2 * math.pi)) % 1.0
    r, g, b = colorsys.hls_to_rgb(hue, 0.66, 0.42)
    return "#%02X%02X%02X" % (int(r * 255), int(g * 255), int(b * 255))


# ── driving it ────────────────────────────────────────────────────────────

def generate(name, upscale=False, dest=None):
    from PIL import Image
    os.makedirs(dest or POOL, exist_ok=True)
    g = graph(PROMPTS[name], SEEDS[name], upscale)
    print("  submitting %s%s ..." % (name, " (4K)" if upscale else ""),
          flush=True)
    hist = wait(submit(g))
    if not hist:
        return None
    src = collect(hist)
    if not src:
        print("  no image came back for", name)
        return None
    im = Image.open(src).convert("RGB")
    if upscale:
        im = im.crop((0, 8, 3840, 2168))          # 2176 -> a clean 2160
    im, k = tone_cap(im)
    out = os.path.join(dest or POOL, name + ".jpg")
    im.save(out, "JPEG", quality=92, optimize=True, progressive=True)
    print("  %-6s %s  %.2f stops down  %d KB"
          % (name, "x".join(map(str, im.size)),
             -__import__("math").log2(max(k, 1e-6)),
             os.path.getsize(out) // 1024))
    return out


def main():
    args = [a for a in sys.argv[1:]]
    if "--rank" in args:
        rows = []
        for f in sorted(os.listdir(POOL)):
            if not f.endswith(".jpg"):
                continue
            p = os.path.join(POOL, f)
            rows.append((calm_score(p), f, measure(p), accent_from(p)))
        rows.sort(reverse=True)
        print("\n%-8s %-6s  %s" % ("name", "calm", "bands that carry text"))
        for sc, f, bands, acc in rows:
            bad = [b for b in bands if not b["ok"]]
            print("%-8s %-6.2f  %s   accent %s"
                  % (f[:-4], sc,
                     "  ".join("%s %.1f:1%s" % (b["band"], b["contrast"],
                                                "" if b["ok"] else " FAIL")
                               for b in bands), acc))
            if bad:
                print("         ^ %d band(s) under floor" % len(bad))
        return
    if "--ship" in args:
        names = args[args.index("--ship") + 1:]
        os.makedirs(SHIP, exist_ok=True)
        for n in names:
            generate(n, upscale=True, dest=SHIP)
        return
    names = [a for a in args if not a.startswith("--")] or list(PROMPTS)
    for n in names:
        generate(n)


if __name__ == "__main__":
    main()
