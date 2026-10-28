"""Projection of a 3D volume onto a plane (SRS FR-7, FR-8; docs/ALGORITHM.md).

We use the "pull" form of the course algorithm (ALGORITHM.md section 4): for every
output pixel (x, y) we compute the 3D point it comes from,

    P(x, y) = mid(y) + (x - Dbc/2) * dp(y)

and read the nearest voxel. A pixel is filled only if its centre lies inside
the triangle/trapezoid:  |x - Dbc/2| <= d12(y) / 2.

All pixels are computed at once with NumPy array operations (no Python loop
per pixel), which is what makes the speed requirement (NFR-1) reachable.
"""
from __future__ import annotations

import numpy as np

from .plane import Plane

_TOL = 1e-9  # guards against floating-point noise on exact boundaries


class Projector:
    """Holds one volume and projects planes from it.

    The volume is indexed M[x][y][z] in voxel coordinates. Creating the
    Projector once and calling project() many times avoids repeating the
    set-up work for every frame of a video.
    """

    def __init__(self, volume: np.ndarray):
        _check_volume(volume)
        self.volume = np.ascontiguousarray(volume)   # no copy if already contiguous
        self.shape = self.volume.shape
        self._flat = self.volume.reshape(-1)          # a view, not a copy
        self._strides = [s // self.volume.itemsize for s in self.volume.strides]

    @staticmethod
    def output_shape(plane: Plane) -> tuple[int, int]:
        """(H, W) of the image: H = ceil(Dab), W = floor(Dbc) + 1  (ALGORITHM.md section 1)."""
        H = int(np.ceil(plane.leg_length - _TOL))
        W = int(np.floor(plane.base_length + _TOL)) + 1
        return H, W

    def project(self, plane: Plane) -> np.ndarray:
        """Return the image E[y, x] of the volume on the plane (same dtype as the volume)."""
        H, W = self.output_shape(plane)
        mid, dp, d12, offset = _row_geometry(plane, H, W)

        # inside the triangle/trapezoid?  |x - Dbc/2| <= d12/2      -> H x W booleans
        ok = np.abs(offset)[None, :] <= d12[:, None] / 2 + _TOL

        # nearest voxel, one axis at a time (keeps temporary arrays small)
        flat_index = np.zeros((H, W), dtype=np.int64)
        for axis in range(3):
            coord = mid[:, axis, None] + offset[None, :] * dp[:, axis, None]   # H x W
            voxel = np.floor(coord + 0.5)                                      # round half up
            ok &= (voxel >= 0) & (voxel < self.shape[axis])                    # inside the volume?
            flat_index += voxel.astype(np.int64) * self._strides[axis]

        image = np.zeros((H, W), dtype=self.volume.dtype)
        image[ok] = self._flat[flat_index[ok]]                                 # outside -> 0 (FR-8)
        return image


def project(volume: np.ndarray, plane: Plane) -> np.ndarray:
    """One-off convenience: project(volume, plane). For many planes use Projector."""
    return Projector(volume).project(plane)


# --------------------------------------------------------------------- helpers
def _row_geometry(plane: Plane, H: int, W: int):
    """Per-row midpoint, row direction and row length, and per-column offset."""
    dab, dbc = plane.leg_length, plane.base_length
    u1 = (plane.b - plane.s1) / dab                     # v(ab): one step down the left leg
    u2 = (plane.c - plane.s2) / dab                     # v(ac): one step down the right leg
    t = np.arange(1, H + 1, dtype=np.float64)[:, None]  # row y is at step y+1 (ALGORITHM.md section 3, #4)
    a1 = plane.s1 + t * u1                              # H x 3
    a2 = plane.s2 + t * u2
    seg = a2 - a1
    d12 = np.linalg.norm(seg, axis=1)                   # length of each row
    dp = seg / np.where(d12 > 0, d12, 1.0)[:, None]     # unit vector along each row
    mid = (a1 + a2) / 2
    offset = np.arange(W, dtype=np.float64) - dbc / 2   # x - Dbc/2 for every column
    return mid, dp, d12, offset


def _check_volume(volume) -> None:
    """FR-2 / FR-3: a 3D integer volume, 1 <= size < 1024 on every axis."""
    if not isinstance(volume, np.ndarray) or volume.ndim != 3:
        raise ValueError(f"expected a 3D volume, got {getattr(volume, 'ndim', '?')} dimensions")
    if not np.issubdtype(volume.dtype, np.integer) or volume.dtype.itemsize > 4:
        raise ValueError(f"voxels must be 8, 16 or 32-bit integers, got {volume.dtype}")
    if min(volume.shape) < 1 or max(volume.shape) >= 1024:
        raise ValueError(f"every size must be in 1..1023, got {volume.shape}")
