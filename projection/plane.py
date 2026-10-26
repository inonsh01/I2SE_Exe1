"""Plane definition and validation (SRS FR-4, FR-5, FR-6).

A plane is given either by 3 points (a, b, c) forming an isosceles triangle,
or by 4 points (a1, a2, b, c) forming an isosceles trapezoid.

Both forms are stored the same way: two "legs" s1 -> b and s2 -> c of equal
length. For a triangle s1 == s2 == a. This lets the projection code handle
both shapes with one algorithm (see docs/ALGORITHM.md §6).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

EPS = 1e-3  # tolerance for comparing lengths (from the assignment)


class PlaneError(ValueError):
    """The given points do not describe a valid plane."""


@dataclass(frozen=True)
class Plane:
    s1: np.ndarray  # start of the left leg  (a, or a1)
    s2: np.ndarray  # start of the right leg (a, or a2)
    b: np.ndarray   # end of the left leg
    c: np.ndarray   # end of the right leg

    @property
    def leg_length(self) -> float:
        """Dab: length of each leg."""
        return float(np.linalg.norm(self.b - self.s1))

    @property
    def base_length(self) -> float:
        """Dbc: length of the base b-c."""
        return float(np.linalg.norm(self.c - self.b))

    @property
    def is_triangle(self) -> bool:
        return bool(np.array_equal(self.s1, self.s2))

    @classmethod
    def from_points(cls, points, eps: float = EPS) -> "Plane":
        """Build a plane from 3 or 4 points (or a flat list of 9 or 12 numbers).

        Raises PlaneError with a message that names the broken rule.
        """
        pts = _to_points(points)
        if len(pts) == 3:
            a, b, c = pts
            _check_triangle(a, b, c, eps)
            return cls(s1=a, s2=a, b=b, c=c)
        a1, a2, b, c = pts
        _check_trapezoid(a1, a2, b, c, eps)
        return cls(s1=a1, s2=a2, b=b, c=c)


# --------------------------------------------------------------------- helpers
def _to_points(points) -> np.ndarray:
    try:
        pts = np.asarray(points, dtype=np.float64)
    except (TypeError, ValueError):
        raise PlaneError("points must be numbers") from None
    if pts.ndim == 1:
        if pts.size not in (9, 12):
            raise PlaneError(f"expected 9 or 12 numbers, got {pts.size}")
        pts = pts.reshape(-1, 3)
    if pts.shape not in ((3, 3), (4, 3)):
        raise PlaneError(f"expected 3 or 4 points with 3 coordinates each, got shape {pts.shape}")
    if not np.all(np.isfinite(pts)):
        raise PlaneError("points must be finite numbers")
    return pts


def _dist(p, q) -> float:
    return float(np.linalg.norm(q - p))


def _check_legs(d1: float, d2: float, eps: float) -> None:
    if d1 < 1.0 or d2 < 1.0:
        raise PlaneError("legs must be at least 1 voxel long")
    if abs(d1 - d2) >= eps:
        raise PlaneError(f"legs differ in length: {d1:.4f} vs {d2:.4f} (EPS = {eps})")


def _check_triangle(a, b, c, eps: float) -> None:
    _check_legs(_dist(a, b), _dist(a, c), eps)
    if _dist(b, c) < eps:
        raise PlaneError("b and c must be different points")
    if np.linalg.norm(np.cross(b - a, c - a)) < eps:
        raise PlaneError("a, b, c are collinear (on one line), so they do not define a plane")


def _check_trapezoid(a1, a2, b, c, eps: float) -> None:
    _check_legs(_dist(a1, b), _dist(a2, c), eps)
    if _dist(b, c) < eps:
        raise PlaneError("b and c must be different points")
    if _dist(a1, a2) > _dist(b, c) + eps:
        raise PlaneError("dist(a1, a2) must be <= dist(b, c)")
    # all 4 points on one plane: a2 must lie on the plane through a1, b, c
    normal = np.cross(b - a1, c - a1)
    n = np.linalg.norm(normal)
    if n < eps:
        raise PlaneError("a1, b, c are collinear (on one line), so they do not define a plane")
    if abs(np.dot(a2 - a1, normal / n)) >= eps:
        raise PlaneError("the four points are not on the same plane")
