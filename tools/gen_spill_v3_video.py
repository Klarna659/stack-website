"""Wan2.2 i2v for the v3 story clips.

Two beats, each its own preset:
  tip       from the upright start frame: the bottle tips over and POURS.
  unsort    from the Kontext-edited organized frame: pills fly OUT of the
            organizer and scatter. Shipped REVERSED (ffmpeg) so on the page
            the pills gather themselves into the compartments — generative
            models can pour, they cannot un-pour, so we film the pour and
            run it backwards.

    python tools/gen_spill_v3_video.py --image tools/hero_pool/spill_v3/upright_a.png --preset tip --seed 101
    python tools/gen_spill_v3_video.py --image ... --preset unsort --seed 202
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, r"C:\AI\persona-hub")
from comfy_lib import post, wait, collect, stage_input

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "tools", "hero_pool", "spill_v3", "video")

W22_HIGH = "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
W22_LOW = "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
W22_LORA_HIGH = "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
W22_LORA_LOW = "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"
TENC = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
VAE = "wan_2.1_vae.safetensors"
FPS = 16
W, H = 1280, 720

PRESETS = {
    "tip": ("the amber pill bottle slowly tips over sideways and falls "
            "onto its side on the counter, capsules and tablets pour out "
            "of its open mouth and scatter and roll across the counter, "
            "the bottle keeps its exact rigid solid three dimensional "
            "shape the whole time, the weekly pill organizer stays "
            "perfectly still, camera locked off on a tripod, no camera "
            "movement, soft steady daylight, photorealistic, tack sharp "
            "focus everywhere, commercial product photography quality, "
            "smooth natural physics"),
    "unsort": ("the pills jump up out of the weekly pill organizer "
               "compartments one after another and scatter and roll "
               "across the counter, the organizer stays perfectly still "
               "and rigid, the tipped amber bottle stays perfectly still, "
               "camera locked off on a tripod, no camera movement, soft "
               "steady daylight, photorealistic, tack sharp focus "
               "everywhere, commercial product photography quality, "
               "stop motion style motion"),
}

NEG = ("static image, no motion, frozen, distorted, warped, melting, "
       "deforming bottle, morphing, blurry, bokeh, depth of field, "
       "low quality, jpeg artifacts, watermark, text, oversaturated, "
       "flickering, jump cut, scene change, people, hands")


def graph(src_name, prompt, seed, length):
    return {
        "HI": {"class_type": "UNETLoader",
               "inputs": {"unet_name": W22_HIGH, "weight_dtype": "default"}},
        "LO": {"class_type": "UNETLoader",
               "inputs": {"unet_name": W22_LOW, "weight_dtype": "default"}},
        "HI_L": {"class_type": "LoraLoaderModelOnly",
                 "inputs": {"model": ["HI", 0], "lora_name": W22_LORA_HIGH,
                            "strength_model": 1.0}},
        "LO_L": {"class_type": "LoraLoaderModelOnly",
                 "inputs": {"model": ["LO", 0], "lora_name": W22_LORA_LOW,
                            "strength_model": 1.0}},
        "HI_S": {"class_type": "ModelSamplingSD3",
                 "inputs": {"model": ["HI_L", 0], "shift": 5.0}},
        "LO_S": {"class_type": "ModelSamplingSD3",
                 "inputs": {"model": ["LO_L", 0], "shift": 5.0}},
        "CLIP": {"class_type": "CLIPLoader",
                 "inputs": {"clip_name": TENC, "type": "wan"}},
        "VAE": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "IMG": {"class_type": "LoadImage", "inputs": {"image": src_name}},
        "SCALE": {"class_type": "ImageScale",
                  "inputs": {"image": ["IMG", 0], "upscale_method": "lanczos",
                             "width": W, "height": H, "crop": "center"}},
        "POS": {"class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["CLIP", 0]}},
        "NEGC": {"class_type": "CLIPTextEncode",
                 "inputs": {"text": NEG, "clip": ["CLIP", 0]}},
        "I2V": {"class_type": "WanImageToVideo", "inputs": {
            "positive": ["POS", 0], "negative": ["NEGC", 0], "vae": ["VAE", 0],
            "width": W, "height": H, "length": length, "batch_size": 1,
            "start_image": ["SCALE", 0]}},
        "KS1": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["HI_S", 0], "add_noise": "enable", "noise_seed": seed,
            "steps": 4, "cfg": 1.0, "sampler_name": "euler",
            "scheduler": "simple",
            "positive": ["I2V", 0], "negative": ["I2V", 1],
            "latent_image": ["I2V", 2],
            "start_at_step": 0, "end_at_step": 2,
            "return_with_leftover_noise": "enable"}},
        "KS2": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["LO_S", 0], "add_noise": "disable", "noise_seed": seed,
            "steps": 4, "cfg": 1.0, "sampler_name": "euler",
            "scheduler": "simple",
            "positive": ["I2V", 0], "negative": ["I2V", 1],
            "latent_image": ["KS1", 0],
            "start_at_step": 2, "end_at_step": 10000,
            "return_with_leftover_noise": "disable"}},
        "DEC": {"class_type": "VAEDecode",
                "inputs": {"samples": ["KS2", 0], "vae": ["VAE", 0]}},
        "VID": {"class_type": "VHS_VideoCombine", "inputs": {
            "images": ["DEC", 0], "frame_rate": FPS, "loop_count": 0,
            "filename_prefix": "spillv3", "format": "video/h264-mp4",
            "pingpong": False, "save_output": True}},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--preset", required=True, choices=sorted(PRESETS))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--seconds", type=float, default=5.0)
    a = ap.parse_args()

    src = a.image if os.path.isabs(a.image) else os.path.join(ROOT, a.image)
    if not os.path.exists(src):
        print("input not found:", src)
        sys.exit(1)
    os.makedirs(DEST, exist_ok=True)

    length = int(round(a.seconds * FPS)) // 4 * 4 + 1
    stem = os.path.splitext(os.path.basename(src))[0]
    name = "%s_%s_s%d" % (a.preset, stem, a.seed)

    staged = stage_input(src, "spillv3_%s.png" % stem)
    print("i2v %s %s seed=%d %df" % (a.preset, stem, a.seed, length),
          flush=True)
    t0 = time.time()
    pid = post(graph(staged, PRESETS[a.preset], a.seed, length))
    hist = wait(pid, timeout=5400)
    got = collect(hist, DEST, name)
    if got:
        print("OK -> %s (%.1f MB, %.0fs)"
              % (got[0], os.path.getsize(got[0]) / 1e6, time.time() - t0),
              flush=True)
    else:
        print("FAILED - no output", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
