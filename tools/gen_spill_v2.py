"""Regenerate the spill hero start frame — v2 brief: SHARP and PROFESSIONAL.

Why v2 exists: the shipped spill2 footage bought its depth with heavy
depth-of-field ("blurred background" was literally in the prompt, per the
FLUX flat-surface gotcha), and the page then stacked a 30px backdrop-blur
scrim behind the headline. Sim's ruling 2026-09-06: the blur reads as
unprofessional mush and the type-behind-bottle graze hides the headline.

The v2 brief inverts both:
  - EVERYTHING IN FOCUS. Commercial still-life is shot at f/8-f/16 or focus
    stacked; the professional tell is crisp texture front to back, not bokeh.
  - The LEFT ~45% of the frame is clean, bright, empty counter — the headline
    sits ON the photograph with no scrim, no blur, no overlap. Legibility is
    bought in the composition, not in CSS.
  - Bottle + spill live in the RIGHT half, pills visible inside the bottle
    (rigidity anchor for Wan), spill reaching toward center but never past it.
  - One coherent world: a real counter against a real wall, warm daylight,
    matching the site's cream ground (#EFE4CC family).

Anti-flat-gradient insurance (the reason v1 blurred its background): the
scene keeps REAL sharp elements — wood grain / stone veining words, a wall
with texture, camera language — so FLUX has something to render instead of
collapsing the empty half into a gradient.

    python tools/gen_spill_v2.py                 generate all directions
    python tools/gen_spill_v2.py studio          one direction
    python tools/gen_spill_v2.py --rank          tone + left-field cleanness
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
POOL = os.path.join(ROOT, "tools", "hero_pool", "spill_v2")

W, H = 1920, 1080

# flux-dev at cfg 1.0 ignores negative conditioning — exclusions must be
# stated positively in the prompt (same note as gen_hero.py).
NEGATIVE = "text, watermark, people, hands, blurry, bokeh, oversaturated"

# Every direction shares the composition contract; they differ in WORLD.
CONTRACT = (
    "a translucent amber pill bottle without a label, white cap off beside it, "
    "tipped over on its side on the right side of the frame, capsules and "
    "tablets visible inside the bottle, more capsules and white tablets "
    "spilled across the surface in front of it reaching toward the center of "
    "the frame, the left half of the frame is clean empty surface with "
    "nothing on it, "
)

STYLE = (
    "professional commercial product photography, shot at f/11 with "
    "everything in tack-sharp focus from front to back, no depth of field "
    "blur, crisp fine texture throughout, soft directional daylight from a "
    "window on the left, gentle long shadows, warm cream and amber palette, "
    "muted colors, subtle film grain, quiet and expensive, 4k advertising "
    "photograph, eye-level camera at a slight downward angle"
)

DIRECTIONS = {
    # A real kitchen, but SHARP — the wall is close and textured, not a
    # bokeh void.
    "kitchen": (CONTRACT +
                "on a pale oak wood kitchen counter with fine visible wood "
                "grain, a clean warm white plaster wall directly behind the "
                "counter in sharp focus, " + STYLE),
    # Studio seamless — the most controlled, least AI-tell world.
    "studio": (CONTRACT +
               "on a smooth warm cream seamless studio surface, the "
               "background a plain warm cream studio wall in sharp focus "
               "with a soft light gradient, " + STYLE),
    # Stone — bright minimal architectural counter.
    "stone": (CONTRACT +
              "on a honed cream travertine stone countertop with fine "
              "natural stone veining, a warm limestone wall directly behind "
              "in sharp focus, " + STYLE),
}

SEEDS = {"kitchen": (411203, 88451, 730914),
         "studio": (204815, 951377, 662041),
         "stone": (317755, 540266, 129983)}


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
                         "denoise": 1.0, "model": ["1", 0],
                         "positive": ["2", 0], "negative": ["3", 0],
                         "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode",
              "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "spillv2", "images": ["6", 0]}},
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
            src = os.path.join(COMFY_OUT, it.get("subfolder", ""),
                               it["filename"])
            if os.path.exists(src):
                return src
    return None


def left_field(path):
    """How clean and bright the headline zone is (left 42%, middle 60% rows).

    The whole point of v2: the type sits on raw photograph. High mean
    luminance + low stddev = a field dark ink can live on. Also reports
    edge density (Laplacian-ish row/col steps) as 'busy'.
    """
    from PIL import Image, ImageStat
    im = Image.open(path).convert("L")
    w, h = im.size
    zone = im.crop((0, int(h * .18), int(w * .42), int(h * .82))).resize((160, 160))
    st = ImageStat.Stat(zone)
    px = list(zone.getdata())
    steps = [abs(px[i] - px[i + 1]) for i in range(len(px) - 1)
             if (i + 1) % 160]
    return {"lum": round(st.mean[0] / 255.0, 3),
            "stddev": round(st.stddev[0], 1),
            "busy": round(sum(steps) / len(steps), 2)}


def sharpness(path):
    """Global focus proxy: mean absolute neighbor step over the RIGHT half
    (where the bottle is). The v1 footage's blurred background scores low
    here; a front-to-back-sharp frame scores high."""
    from PIL import Image
    im = Image.open(path).convert("L")
    w, h = im.size
    zone = im.crop((int(w * .5), 0, w, h)).resize((200, 200))
    px = list(zone.getdata())
    steps = [abs(px[i] - px[i + 1]) for i in range(len(px) - 1) if (i + 1) % 200]
    return round(sum(steps) / len(steps), 2)


def generate(names):
    os.makedirs(POOL, exist_ok=True)
    for name in names:
        for i, seed in enumerate(SEEDS[name]):
            tag = "%s_%s" % (name, "abc"[i])
            out = os.path.join(POOL, tag + ".png")
            if os.path.exists(out):
                print("skip", tag, flush=True)
                continue
            t0 = time.time()
            pid = submit(graph(DIRECTIONS[name], seed))
            hist = wait(pid)
            src = collect(hist) if hist else None
            if not src:
                print("FAILED", tag, flush=True)
                continue
            from PIL import Image
            Image.open(src).save(out)
            print("%-10s %5.0fs  left %s  sharp %.2f"
                  % (tag, time.time() - t0, left_field(out), sharpness(out)),
                  flush=True)


def rank():
    for f in sorted(os.listdir(POOL)):
        if f.endswith(".png"):
            p = os.path.join(POOL, f)
            print("%-12s left %s  sharp %.2f"
                  % (f[:-4], left_field(p), sharpness(p)))


def main():
    args = sys.argv[1:]
    if args and args[0] == "--rank":
        rank()
        return
    generate(args or list(DIRECTIONS))


if __name__ == "__main__":
    main()
