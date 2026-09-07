"""FLUX Kontext instruction edit — scene-object edits for the hero frames.

Lean version of persona-hub's cami_edit.py graph (no identity/refine pass):
same model, same official template settings (euler/simple, 20 steps,
cfg 1, guidance 2.5).

    python tools/kontext_edit.py --image <path> --edit "..." --name out_name [--seed N]

Output lands next to the input image as <name>.png.
"""
import argparse
import os
import shutil
import sys
import time

sys.path.insert(0, r"C:\AI\persona-hub")
from comfy_lib import post, wait, stage_input, OUTPUT


def collect_image(hist, dest_dir, out_name):
    """comfy_lib.collect only copies video files; SaveImage outputs PNGs."""
    for _, out in (hist.get("outputs") or {}).items():
        for it in out.get("images", []):
            src = os.path.join(OUTPUT, it.get("subfolder", ""),
                               it["filename"])
            if os.path.exists(src):
                dst = os.path.join(dest_dir, out_name + ".png")
                shutil.copy(src, dst)
                return dst
    return None

MODEL = "flux1-dev-kontext_fp8_scaled.safetensors"
CLIP_L = "clip_l.safetensors"
T5 = "t5xxl_fp8_e4m3fn.safetensors"
VAE = "ae.safetensors"


def graph(staged, instruction, seed):
    return {
        "UNET": {"class_type": "UNETLoader",
                 "inputs": {"unet_name": MODEL, "weight_dtype": "default"}},
        "CLIP": {"class_type": "DualCLIPLoader",
                 "inputs": {"clip_name1": CLIP_L, "clip_name2": T5,
                            "type": "flux"}},
        "VAE": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "IMG": {"class_type": "LoadImage", "inputs": {"image": staged}},
        "SCALE": {"class_type": "FluxKontextImageScale",
                  "inputs": {"image": ["IMG", 0]}},
        "ENC": {"class_type": "VAEEncode",
                "inputs": {"pixels": ["SCALE", 0], "vae": ["VAE", 0]}},
        "POS": {"class_type": "CLIPTextEncode",
                "inputs": {"text": instruction, "clip": ["CLIP", 0]}},
        "REF": {"class_type": "ReferenceLatent",
                "inputs": {"conditioning": ["POS", 0], "latent": ["ENC", 0]}},
        "GUIDE": {"class_type": "FluxGuidance",
                  "inputs": {"conditioning": ["REF", 0], "guidance": 2.5}},
        "NEGT": {"class_type": "CLIPTextEncode",
                 "inputs": {"text": "", "clip": ["CLIP", 0]}},
        "NEG": {"class_type": "ConditioningZeroOut",
                "inputs": {"conditioning": ["NEGT", 0]}},
        "KS": {"class_type": "KSampler", "inputs": {
            "model": ["UNET", 0], "seed": seed, "steps": 20, "cfg": 1.0,
            "sampler_name": "euler", "scheduler": "simple",
            "positive": ["GUIDE", 0], "negative": ["NEG", 0],
            "latent_image": ["ENC", 0], "denoise": 1.0}},
        "DEC": {"class_type": "VAEDecode",
                "inputs": {"samples": ["KS", 0], "vae": ["VAE", 0]}},
        "SAVE": {"class_type": "SaveImage",
                 "inputs": {"images": ["DEC", 0],
                            "filename_prefix": "kontext_hero"}},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--edit", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    src = os.path.abspath(a.image)
    dest_dir = os.path.dirname(src)
    staged = stage_input(src, "kontext_%s%s" % (
        os.path.splitext(os.path.basename(src))[0],
        os.path.splitext(src)[1]))
    t0 = time.time()
    pid = post(graph(staged, a.edit, a.seed))
    hist = wait(pid, timeout=1800)
    got = collect_image(hist, dest_dir, a.name)
    if got:
        print("OK -> %s (%.0fs)" % (got, time.time() - t0), flush=True)
    else:
        print("FAILED", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
