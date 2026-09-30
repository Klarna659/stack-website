"""v4 frames: the CINEMATIC cut sequence (Sim's 2026-09-06 late ruling).

One static wide take read as amateur; v4 is three SHOTS cut together:
  A  medium: bottle tips + pours (reuses spill_v3/upright_c_open.png,
     camera push-in prompted at the Wan stage)
  B  close-up at counter level: pills tumbling out of the mouth
  C  payoff: camera pulls back — a phone on the counter runs the real
     Stack list and the pills lie in neat rows beside it. Filmed reversed
     (pills leap OUT + camera pushes IN -> played backwards) so the final
     cut pulls out while the pills organize. The phone screen gets the
     REAL app UI composited on before the Wan pass (comp_screen.py).

Same world words as v3 (travertine + limestone), same no-blur law.

    python tools/gen_spill_v4.py
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
POOL = os.path.join(ROOT, "tools", "hero_pool", "spill_v4")

W, H = 1920, 1080
NEGATIVE = "text, watermark, people, hands, blurry, bokeh, oversaturated"

WORLD = ("on a honed cream travertine stone countertop with fine natural "
         "stone veining, a warm limestone wall behind in sharp focus, "
         "professional commercial product photography, everything in "
         "tack-sharp focus from front to back, no depth of field blur, "
         "crisp fine texture, soft directional daylight from a window on "
         "the left, gentle long shadows, warm cream and amber palette, "
         "muted colors, subtle film grain, quiet and expensive, 4k "
         "advertising photograph")

FRAMES = {
    # Shot B start: close, low, at the mouth — pills mid-tumble.
    "closeup": ("low camera angle at counter level, a close up of a "
                "tipped translucent amber pill bottle lying on its side, "
                "yellow capsules and white oblong tablets tumbling out of "
                "its open mouth and rolling toward the camera across the "
                "stone, a few pills mid-roll, the bottle fills the right "
                "half of the frame, " + WORLD),
    # Shot C end state: phone + neat rows, bottle far background.
    "phone": ("a modern smartphone with a dark screen lying flat on the "
              "counter tilted at a slight angle on the RIGHT side of the "
              "frame, yellow capsules and white oblong tablets arranged "
              "in several neat straight horizontal rows on the counter "
              "left of center like a tidy checklist, the tipped empty "
              "amber pill bottle small in the far right background, "
              "the left third of the frame is clean empty counter, "
              "seen from a three quarter high angle, " + WORLD),
}

SEEDS = {"closeup": (818041, 550913, 132708),
         "phone": (441772, 118530, 967204)}


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
              "inputs": {"filename_prefix": "spillv4", "images": ["6", 0]}},
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
            print("%-10s %5.0fs" % (tag, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
