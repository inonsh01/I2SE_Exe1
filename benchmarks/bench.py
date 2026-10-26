"""Speed test (NFR-1, TC-F1 / TC-F2): planes projected per second.

Usage:
    python benchmarks/bench.py                     # random 500^3 volume (TC-F1)
    python benchmarks/bench.py data/CTACardio.nrrd # a real scan (TC-F2)
"""
import platform
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from projection import Plane, Projector  # noqa: E402
from projection.io import load_volume  # noqa: E402

N_PLANES = 100


def rotating_planes(shape, n=N_PLANES):
    """n square planes through the centre of the volume, at different angles."""
    centre = (np.array(shape) - 1) / 2
    half = max(shape) / 2
    planes = []
    for t in np.linspace(0, np.pi, n, endpoint=False):
        down = np.array([np.cos(t), np.sin(t), 0.3]); down /= np.linalg.norm(down)
        across = np.cross(down, [0, 0, 1.0]); across /= np.linalg.norm(across)
        top, bottom = centre - half * down, centre + half * down
        planes.append(Plane.from_points([top - half * across, top + half * across,
                                         bottom - half * across, bottom + half * across]))
    return planes


def main():
    if len(sys.argv) > 1:
        volume, name = load_volume(sys.argv[1]), Path(sys.argv[1]).name
    else:
        volume, name = np.random.default_rng(0).integers(0, 256, (500, 500, 500), dtype=np.uint8), "random 500^3"
    projector = Projector(volume)
    planes = rotating_planes(volume.shape)
    projector.project(planes[0])  # warm-up
    start = time.perf_counter()
    for p in planes:
        projector.project(p)
    seconds = time.perf_counter() - start
    fps = len(planes) / seconds
    h, w = projector.output_shape(planes[0])
    print(f"{name} {volume.shape} {volume.dtype}: {len(planes)} planes of {h}x{w} pixels")
    print(f"-> {fps:.0f} planes per second  ({'PASS' if fps >= 30 else 'FAIL'}: need >= 30, target >= 100)")
    print(f"machine: {platform.machine()}, {platform.system()}, Python {platform.python_version()}, NumPy {np.__version__}")


if __name__ == "__main__":
    main()
