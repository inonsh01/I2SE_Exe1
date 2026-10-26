"""Create the animated GIFs shown in the README (GitHub shows GIFs inline, not MP4s).

Usage: python docs/media/make_gifs.py   (needs data/MRHead.nrrd and data/MRBrainTumor1.nrrd)
"""
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from projection import Plane, Projector  # noqa: E402
from projection.io import intensity_window, load_volume, to_uint8  # noqa: E402

OUT = Path(__file__).resolve().parent


def read_rows(path):
    with open(path) as f:
        return [[float(v) for v in r] for r in csv.reader(f) if r and not r[0].startswith("#")]


def make_gif(scan, csv_name, gif_name, step, scale=1.5, ms=90):
    volume = load_volume(ROOT / "data" / f"{scan}.nrrd")
    lo, hi = intensity_window(volume)
    proj = Projector(volume)
    frames = [to_uint8(proj.project(Plane.from_points(r)), lo, hi) for r in read_rows(ROOT / "examples" / csv_name)[::step]]
    H, W = max(f.shape[0] for f in frames), max(f.shape[1] for f in frames)
    images = []
    for f in frames:
        canvas = np.zeros((H, W), np.uint8)
        y0, x0 = (H - f.shape[0]) // 2, (W - f.shape[1]) // 2
        canvas[y0:y0 + f.shape[0], x0:x0 + f.shape[1]] = f
        img = Image.fromarray(canvas).resize((int(W * scale), int(H * scale)), Image.BILINEAR)
        images.append(img.convert("P", palette=Image.ADAPTIVE, colors=64))
    images[0].save(OUT / gif_name, save_all=True, append_images=images[1:], duration=ms, loop=0, optimize=True)
    print(f"{gif_name}: {len(images)} frames, {(OUT / gif_name).stat().st_size / 1e6:.1f} MB")


make_gif("MRHead", "rotating.csv", "mrhead_rotating.gif", step=2)
make_gif("MRHead", "axial_sweep.csv", "mrhead_axial_sweep.gif", step=3)
make_gif("MRHead", "triangles.csv", "mrhead_triangles.gif", step=1, ms=120)
make_gif("MRBrainTumor1", "MRBrainTumor1_rotating.csv", "tumor_rotating.gif", step=2)
