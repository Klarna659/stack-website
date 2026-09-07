"""v3 start frame: the FULL story needs an upright bottle and an organizer.

Sim's 2026-09-06 ruling on v2: the clip must SHOW the story — bottle tips,
pills pour, then visibly reorganize into a weekly pill organizer. So the
start frame is the moment before it happens: upright amber bottle (pills
visible), cap off, an OPEN EMPTY weekly organizer sitting in the scene
from frame one (set dressing — so the organize beat later has perfect
continuity), left field clean for the type. Same stone world, same sharp
f/11 brief as v2 (no blur — standing law).

    python tools/gen_spill_v3.py
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
POOL = os.path.join(ROOT, "tools", "hero_pool", "spill_v3")

W, H = 1920, 1080
NEGATIVE = "text, watermark, people, hands, blurry, bokeh, oversaturated"

PROMPT = (
    "a translucent amber plastic pill bottle standing upright on the right "
    "side of the frame, capsules and tablets visible inside it, its white "
    "cap lying on the counter beside it, an open empty weekly pill "
    "organizer with seven small compartments sitting flat on the counter "
    "in the middle of the frame with all lids open, the left third of the "
    "frame is clean empty counter with nothing on it, "
    "on a honed cream travertine stone countertop with fine natural stone "
    "veining, a warm limestone wall directly behind in sharp focus, "
    "professional commercial product photography, shot at f/11 with "
    "everything in tack-sharp focus from front to back, no depth of field "
    "blur, crisp fine texture throughout, soft directional daylight from a "
    "window on the left, gentle long shadows, warm cream and amber "
    "palette, muted colors, subtle film grain, quiet and expensive, 4k "
    "advertising photograph, eye-level camera at a slight downward angle"
)

SEEDS = (274119, 660351, 903472)


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
              "inputs": {"filename_prefix": "spillv3", "images": ["6", 0]}},
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
    for i, seed in enumerate(SEEDS):
        tag = "upright_%s" % "abc"[i]
        out = os.path.join(POOL, tag + ".png")
        if os.path.exists(out):
            print("skip", tag, flush=True)
            continue
        t0 = time.time()
        pid = submit(graph(PROMPT, seed))
        hist = wait(pid)
        src = collect(hist) if hist else None
        if not src:
            print("FAILED", tag, flush=True)
            continue
        from PIL import Image
        Image.open(src).save(out)
        print("%-10s %5.0fs" % (tag, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
