"""Generate small synthetic NRRD volumes whose correct cuts are known in advance.

Usage:
    python data/make_synthetic.py
"""
from pathlib import Path

import nrrd
import numpy as np

HERE = Path(__file__).resolve().parent


def cube(n: int = 64) -> np.ndarray:
    """uint8: black volume with a bright cube in the middle (value 200).
    Any cut through the centre must show a bright square/polygon on black."""
    v = np.zeros((n, n, n), dtype=np.uint8)
    q = n // 4
    v[q:n - q, q:n - q, q:n - q] = 200
    return v


def gradient(n: int = 64) -> np.ndarray:
    """uint16: value = 1000 * x. A cut at x = const must be one flat colour;
    a cut along x must change evenly from left to right."""
    x = np.arange(n, dtype=np.uint16)[:, None, None] * 1000
    return np.broadcast_to(x, (n, n, n)).copy()


def sphere(n: int = 64) -> np.ndarray:
    """uint32: a ball of radius n/3 (value 100000). Every cut through the centre
    must show a circle of the same size, whatever the angle."""
    c = (n - 1) / 2
    x, y, z = np.ogrid[:n, :n, :n]
    inside = (x - c) ** 2 + (y - c) ** 2 + (z - c) ** 2 <= (n / 3) ** 2
    return np.where(inside, 100000, 0).astype(np.uint32)


def odd_shape() -> np.ndarray:
    """uint8: a non-cubic volume (10 x 40 x 25) with a different value in each
    corner, to catch mixed-up axes."""
    v = np.zeros((10, 40, 25), dtype=np.uint8)
    v[0, 0, 0], v[-1, 0, 0], v[0, -1, 0], v[0, 0, -1] = 50, 100, 150, 250
    return v


VOLUMES = {
    "synthetic_cube.nrrd": cube,
    "synthetic_gradient.nrrd": gradient,
    "synthetic_sphere.nrrd": sphere,
    "synthetic_odd_shape.nrrd": odd_shape,
}


def main() -> None:
    for name, make in VOLUMES.items():
        vol = make()
        nrrd.write(str(HERE / name), vol, index_order="F")
        print(f"{name}: {vol.shape} {vol.dtype}")


if __name__ == "__main__":
    main()
