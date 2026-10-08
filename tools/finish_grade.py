"""Finishing grade — make assets read 'clean, 4K, smooth' (Sim's
2026-09-07 calibration on the reference TikToks: the common denominator
is asset fidelity, not mechanics).

Two passes, all local:
  1. DETAIL: every frame through 4x-UltraSharp (ComfyUI, VHS batch),
     then scaled to the delivery size — kills the 720p softness.
  2. MOTION: ffmpeg minterpolate 16fps -> 48fps — kills the stepping.

    python tools/finish_grade.py video <in.mp4> <out.mp4> [--width 2560]
    python tools/finish_grade.py still <in.png> <out.jpg> [--width 1800]
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:8188"
COMFY_IN = r"C:\AI\ComfyUI_windows_portable\ComfyUI\input"
COMFY_OUT = r"C:\AI\ComfyUI_windows_portable\ComfyUI\output"
MODEL = "4x-UltraSharp.pth"


def submit(g):
    data = json.dumps({"prompt": g}).encode()
    req = urllib.request.Request(BASE + "/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))["prompt_id"]


def wait(pid, timeout=5400):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            h = json.load(urllib.request.urlopen(
                "%s/history/%s" % (BASE, pid), timeout=30))
        except Exception:
            time.sleep(2)
            continue
        if pid in h and h[pid].get("outputs"):
            return h[pid]
        if pid in h:
            for m in h[pid].get("status", {}).get("messages", []):
                if m and m[0] == "execution_error":
                    print("EXEC ERROR:", json.dumps(m)[:1500], flush=True)
                    return None
        time.sleep(2)
    raise TimeoutError(pid)


def video_graph(name, w, h):
    return {
        "L": {"class_type": "VHS_LoadVideo",
              "inputs": {"video": name, "force_rate": 0,
                         "custom_width": 0, "custom_height": 0,
                         "frame_load_cap": 0, "skip_first_frames": 0,
                         "select_every_nth": 1}},
        "M": {"class_type": "UpscaleModelLoader",
              "inputs": {"model_name": MODEL}},
        "U": {"class_type": "ImageUpscaleWithModel",
              "inputs": {"upscale_model": ["M", 0], "image": ["L", 0]}},
        "S": {"class_type": "ImageScale",
              "inputs": {"image": ["U", 0], "upscale_method": "lanczos",
                         "width": w, "height": h, "crop": "disabled"}},
        "V": {"class_type": "VHS_VideoCombine",
              "inputs": {"images": ["S", 0], "frame_rate": 16,
                         "loop_count": 0, "filename_prefix": "finish",
                         "format": "video/h264-mp4", "pingpong": False,
                         "save_output": True, "crf": 12}},
    }


def collect_video(hist):
    for _, out in (hist.get("outputs") or {}).items():
        for key in ("gifs", "videos"):
            for it in out.get(key, []):
                fn = it.get("filename", "")
                if fn.endswith(".mp4"):
                    p = os.path.join(COMFY_OUT, it.get("subfolder", ""), fn)
                    if os.path.exists(p):
                        return p
    return None


def probe_size(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
        text=True).strip()
    return [int(x) for x in out.split(",")]


def do_video(src, dst, width):
    sw, sh = probe_size(src)
    height = round(width * sh / sw / 2) * 2
    import shutil
    staged = os.path.join(COMFY_IN, "finish_" + os.path.basename(src))
    shutil.copy(src, staged)
    print("upscaling %s -> %dx%d…" % (os.path.basename(src), width, height),
          flush=True)
    pid = submit(video_graph(os.path.basename(staged), width, height))
    hist = wait(pid)
    up = collect_video(hist) if hist else None
    if not up:
        print("upscale FAILED")
        sys.exit(1)
    print("interpolating 16 -> 48 fps…", flush=True)
    subprocess.check_call(
        ["ffmpeg", "-y", "-v", "error", "-i", up,
         "-vf", "minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:vsbmc=1",
         "-c:v", "libx264", "-crf", "20", "-g", "24", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", dst])
    print("done ->", dst, round(os.path.getsize(dst) / 1024), "KB")


def still_graph(name, w, h):
    return {
        "L": {"class_type": "LoadImage", "inputs": {"image": name}},
        "M": {"class_type": "UpscaleModelLoader",
              "inputs": {"model_name": MODEL}},
        "U": {"class_type": "ImageUpscaleWithModel",
              "inputs": {"upscale_model": ["M", 0], "image": ["L", 0]}},
        "S": {"class_type": "ImageScale",
              "inputs": {"image": ["U", 0], "upscale_method": "lanczos",
                         "width": w, "height": h, "crop": "disabled"}},
        "V": {"class_type": "SaveImage",
              "inputs": {"images": ["S", 0], "filename_prefix": "finishimg"}},
    }


def do_still(src, dst, width):
    from PIL import Image
    im = Image.open(src)
    height = round(width * im.height / im.width / 2) * 2
    import shutil
    staged = os.path.join(COMFY_IN, "finish_" + os.path.basename(src))
    shutil.copy(src, staged)
    print("upscaling still -> %dx%d…" % (width, height), flush=True)
    pid = submit(still_graph(os.path.basename(staged), width, height))
    hist = wait(pid)
    out = None
    for _, o in (hist.get("outputs") or {}).items():
        for it in o.get("images", []):
            p = os.path.join(COMFY_OUT, it.get("subfolder", ""),
                             it["filename"])
            if os.path.exists(p):
                out = p
    if not out:
        print("upscale FAILED")
        sys.exit(1)
    Image.open(out).convert("RGB").save(dst, "JPEG", quality=84,
                                        optimize=True, progressive=True)
    print("done ->", dst, round(os.path.getsize(dst) / 1024), "KB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["video", "still"])
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--width", type=int, default=None)
    a = ap.parse_args()
    width = a.width or (2560 if a.mode == "video" else 1800)
    if a.mode == "video":
        do_video(a.src, a.dst, width)
    else:
        do_still(a.src, a.dst, width)


if __name__ == "__main__":
    main()
