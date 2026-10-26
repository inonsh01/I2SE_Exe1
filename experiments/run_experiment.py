"""Step 8 experiment: run the demo on every scan of the data set and measure speed.

For each real scan it:
  1. writes a CSV of 90 rectangles through the centre, rotating half a turn
     around the scan's 3rd axis (examples/<scan>_rotating.csv),
  2. runs the demo on it (results/<scan>_rotating.mp4) and saves 3 sample
     frames as PNG (start, 1/4 and 1/2 of the turn),
  3. times 100 projections (TC-F2).
Then it times the random 500^3 volume (TC-F1) and prints a results table.

Usage: python experiments/run_experiment.py
"""
import csv
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import Ex0  # noqa: E402
from projection import Plane, Projector  # noqa: E402
from projection.io import intensity_window, load_volume, to_uint8  # noqa: E402

SCANS = ["MRHead", "MRBrainTumor1", "CTChest", "CTACardio"]
N_FRAMES = 90


def rotating_planes(shape, n=N_FRAMES):
    """Rectangles through the centre that contain axis 2 and turn in the axis-0/axis-1 plane."""
    c = (np.array(shape, dtype=float) - 1) / 2
    half_h, half_w = max(shape[0], shape[1]) / 2, (shape[2] - 1) / 2
    across = np.array([0.0, 0.0, 1.0])
    out = []
    for t in np.linspace(0, np.pi, n, endpoint=False):
        down = np.array([np.cos(t), np.sin(t), 0.0])
        top, bot = c - half_h * down, c + half_h * down
        out.append([top - half_w * across, top + half_w * across, bot - half_w * across, bot + half_w * across])
    return out


def write_csv(path, planes):
    with open(path, "w", newline="") as f:
        f.write("# 90 rectangles through the centre, rotating half a turn (made by experiments/run_experiment.py)\n")
        w = csv.writer(f)
        for p in planes:
            w.writerow([f"{v:.3f}".rstrip("0").rstrip(".") for v in np.ravel(p)])


def time_projections(volume, planes, repeat=100):
    proj = Projector(volume)
    planes = [Plane.from_points(p) for p in planes]
    proj.project(planes[0])
    sel = [planes[i % len(planes)] for i in range(repeat)]
    t = time.perf_counter()
    for p in sel:
        proj.project(p)
    return repeat / (time.perf_counter() - t), proj.output_shape(planes[0])


def main():
    import imageio.v2 as imageio
    rows = []
    for name in SCANS:
        path = ROOT / "data" / f"{name}.nrrd"
        if not path.is_file():
            print(f"{name}: missing, run  python data/download_data.py {name}")
            continue
        volume = load_volume(path)
        planes = rotating_planes(volume.shape)
        csv_path = ROOT / "examples" / f"{name}_rotating.csv"
        write_csv(csv_path, planes)
        print(f"\n--- {name} ---")
        Ex0.main([str(path), str(csv_path), str(ROOT / "results" / f"{name}_rotating.mp4"), "--fps", "15"])
        lo, hi = intensity_window(volume)
        proj = Projector(volume)
        for k in (0, N_FRAMES // 4, N_FRAMES // 2):
            img = to_uint8(proj.project(Plane.from_points(planes[k])), lo, hi)
            imageio.imwrite(ROOT / "results" / f"{name}_frame{k:02d}.png", img)
        fps, (h, w) = time_projections(volume, planes)
        rows.append((name, volume.shape, volume.dtype, f"{h}×{w}", fps))

    vol = np.random.default_rng(0).integers(0, 256, (500, 500, 500), dtype=np.uint8)
    fps, (h, w) = time_projections(vol, rotating_planes(vol.shape))
    rows.append(("random 500³", vol.shape, vol.dtype, f"{h}×{w}", fps))

    print("\n| Volume | Size | Type | Frame (rows×cols) | Planes per second |")
    print("| --- | --- | --- | --- | --- |")
    for name, shape, dtype, frame, fps in rows:
        print(f"| {name} | {'×'.join(map(str, shape))} | {dtype} | {frame} | {fps:,.0f} |")
    print(f"\nMachine: {platform.machine()}, {platform.system()}, Python {platform.python_version()}, NumPy {np.__version__}")


if __name__ == "__main__":
    main()
