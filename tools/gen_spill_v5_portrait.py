"""Portrait (9:16) start frames for the MOBILE film.

Sim's 2026-09-07 ruling: the mobile framed-card treatment reads amateur.
The research brief was explicit — professional product sites shoot a
DEDICATED vertical version, they never scale the desktop asset down. So
mobile gets its own three-shot film at 720x1280, full-bleed, copy over
the clean upper third. Same world, same laws (sharp, no blur).

    python tools/gen_spill_v5_portrait.py
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
POOL = os.path.join(ROOT, "tools", "hero_pool", "spill_v5p")

W, H = 1080, 1920
NEGATIVE = "text, watermark, people, hands, blurry, bokeh, oversaturated"

WORLD = ("on a honed cream travertine stone countertop with fine natural "
         "stone veining, a warm limestone wall filling the background in "
         "sharp focus, professional commercial product photography, "
         "everything in tack-sharp focus from front to back, no depth of "
         "field blur, crisp fine texture, soft directional daylight from "
         "a window on the left, gentle long shadows, warm cream and amber "
         "palette, muted colors, subtle film grain, quiet and expensive, "
         "4k advertising photograph, vertical composition, the upper "
         "third of the frame is clean empty wall")

FRAMES = {
    "uprightP": ("an upright translucent amber pill bottle standing open "
                 "in the lower half of the frame slightly right of "
                 "center, yellow capsules and white tablets visible "
                 "inside it, its white cap lying on the counter beside "
                 "it, nothing else on the counter, " + WORLD),
    "closeupP": ("a close up low camera angle at counter level of a "
                 "tipped translucent amber pill bottle lying on its side "
                 "in the lower half of the frame, yellow capsules and "
                 "white tablets tumbling out of its open mouth toward "
                 "the camera, a few pills mid-roll, " + WORLD),
    "phoneP": ("a modern smartphone with a dark screen lying flat on the "
               "counter in the lower half of the frame seen from a high "
               "three quarter angle so its screen faces the camera, "
               "yellow capsules and white tablets arranged in neat "
               "little rows on the counter just left of the phone, the "
               "tipped empty amber pill bottle small behind it, " + WORLD),
}

SEEDS = {"uprightP": (516103, 88427, 730081),
         "closeupP": (204551, 660912, 341008),
         "phoneP": (912744, 155390, 468225)}


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
              "inputs": {"filename_prefix": "spillv5p", "images": ["6", 0]}},
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


def main():
    os.makedirs(POOL, exist_ok=True)
    for name in (sys.argv[1:] or list(FRAMES)):
        for i, seed in enumerate(SEEDS[name]):
            tag = "%s_%s" % (name, "abc"[i])
            out = os.path.join(POOL, tag + ".png")
            if os.path.exists(out):
                print("skip", tag, flush=True)
                continue
            t0 = time.time()
            pid = submit(graph(FRAMES[name], seed))
            hist = wait(pid)
            src = collect(hist) if hist else None
            if not src:
                print("FAILED", tag, flush=True)
                continue
            from PIL import Image
            Image.open(src).save(out)
            print("%-11s %5.0fs" % (tag, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
